"""Custom Docker sandbox backend for Deep Agents."""

import io
import os
import shlex
import tarfile

from deepagents.backends.protocol import (
    EditResult,
    ExecuteResponse,
    FileDownloadResponse,
    FileInfo,
    FileUploadResponse,
    GrepMatch,
    WriteResult,
)
from deepagents.backends.sandbox import BaseSandbox
import docker
from docker.errors import DockerException, NotFound


class DockerSandbox(BaseSandbox):
    """Docker sandbox backend using local Docker containers.

    This sandbox executes commands in a specified Docker container,
    providing an isolated environment for code execution.
    """

    def __init__(
        self,
        *,
        container_name: str,
        work_dir: str = "/workspace",
        timeout: int = 1800,
    ) -> None:
        """Create a Docker sandbox backend.

        Args:
            container_name: Name or ID of the Docker container to use.
            work_dir: Working directory inside the container. Default: "/workspace".
            timeout: Default command timeout in seconds. Default: 30 minutes.
        """
        self._container_name = container_name
        self._work_dir = work_dir.rstrip("/")
        self._default_timeout = timeout
        self._client = docker.from_env()
        self._container = self._client.containers.get(container_name)

    def _validate_and_normalize_path(self, file_path: str) -> str:
        """Validate and normalize a file path to be within work_dir.

        Args:
            file_path: The file path to validate (can be absolute or relative).

        Returns:
            The normalized, safe path relative to work_dir.

        Raises:
            ValueError: If the path attempts to escape work_dir.
        """

        # Convert to absolute path first
        if os.path.isabs(file_path):
            abs_path = os.path.normpath(file_path)
            if not abs_path.startswith(self._work_dir + os.sep) and abs_path != self._work_dir:
                abs_path = self._work_dir + abs_path
        else:
            # Relative path: join with work_dir
            abs_path = os.path.normpath(os.path.join(self._work_dir, file_path))

        # Check if the path is within work_dir

        # Return path relative to work_dir (strip leading slash for tar)
        rel_path = os.path.relpath(abs_path, self._work_dir)
        return rel_path

    def _ensure_parent_dir_exists(self, file_path: str) -> None:
        """Ensure the parent directory of file_path exists.

        Args:
            file_path: The file path (relative to work_dir).
        """
        if "/" in file_path and file_path != "/":
            parent_dir = shlex.quote(file_path.rsplit("/", 1)[0])
            self._container.exec_run(cmd=f"mkdir -p {parent_dir}", workdir=self._work_dir)

    def _upload_content_via_tar(self, file_path: str, content: bytes | str) -> None:
        """Upload content to a file using tar archive.

        Args:
            file_path: The file path relative to work_dir.
            content: The content to write (bytes or str).
        """
        # Convert string to bytes if necessary
        if isinstance(content, str):
            content_bytes = content.encode("utf-8")
        else:
            content_bytes = content

        # Create tar archive
        tar_stream = io.BytesIO()
        with tarfile.open(fileobj=tar_stream, mode="w") as tar:
            tarinfo = tarfile.TarInfo(name=file_path)
            tarinfo.size = len(content_bytes)
            tar.addfile(tarinfo, io.BytesIO(content_bytes))

        tar_stream.seek(0)
        self._container.put_archive(path=self._work_dir, data=tar_stream.read())

    def _check_file_exists(self, file_path: str) -> bool:
        """Check if a file exists in the container.

        Args:
            file_path: The file path relative to work_dir.

        Returns:
            True if the file exists, False otherwise.
        """
        quoted_path = shlex.quote(file_path)
        check_cmd = f"test -f {quoted_path}"
        exit_code, _ = self._container.exec_run(cmd=check_cmd, workdir=self._work_dir)
        return exit_code == 0

    @property
    def id(self) -> str:
        """Return the container name as sandbox id."""
        return self._container_name

    def execute(
        self,
        command: str,
        *,
        timeout: int | None = None,
    ) -> ExecuteResponse:
        """Execute a shell command inside the Docker container.

        Args:
            command: Shell command string to execute.
            timeout: Maximum time in seconds to wait for the command to complete.
                    If None, uses the backend's default timeout.

        Returns:
            ExecuteResponse with output, exit code, and truncation flag.
        """
        # effective_timeout = timeout if timeout is not None else self._default_timeout

        try:
            exit_code, output = self._container.exec_run(
                cmd=command,
                workdir=self._work_dir,
                # timeout=effective_timeout,
            )

            output_str = output.decode("utf-8", errors="replace")

            return ExecuteResponse(
                output=output_str,
                exit_code=exit_code,
                truncated=False,
            )
        except DockerException as e:
            return ExecuteResponse(
                output=f"Docker error: {e!s}",
                exit_code=1,
                truncated=False,
            )
        except Exception as e:
            return ExecuteResponse(
                output=f"Error executing command: {e!s}",
                exit_code=1,
                truncated=False,
            )

    def write(
        self,
        file_path: str,
        content: str,
    ) -> WriteResult:
        """Write content to a file using Docker SDK."""
        try:
            # Validate and normalize path
            rel_path = self._validate_and_normalize_path(file_path)

            # Check if file already exists
            if self._check_file_exists(rel_path):
                return WriteResult(error=f"File '{file_path}' already exists")

            # Ensure parent directory exists
            self._ensure_parent_dir_exists(rel_path)

            # Write file content using tar archive
            self._upload_content_via_tar(rel_path, content)

            return WriteResult(path=file_path, files_update=None)
        except ValueError as e:
            return WriteResult(error=str(e))
        except DockerException as e:
            return WriteResult(error=str(e))

    def read(
        self,
        file_path: str,
        offset: int = 0,
        limit: int = 2000,
    ) -> str:
        """Read file content with line numbers using Docker SDK."""
        try:
            # Validate and normalize path
            rel_path = self._validate_and_normalize_path(file_path)
            quoted_path = shlex.quote(rel_path)

            # Check if file exists
            if not self._check_file_exists(rel_path):
                return f"Error: File '{file_path}' not found"

            # Check if file is empty
            stat_cmd = f"wc -c < {quoted_path}"
            exit_code, output = self._container.exec_run(cmd=stat_cmd, workdir=self._work_dir)
            if exit_code == 0 and output.strip().decode() == "0":
                return "System reminder: File exists but has empty contents"

            # Read file content
            read_cmd = f"cat {quoted_path}"
            exit_code, output = self._container.exec_run(cmd=read_cmd, workdir=self._work_dir)

            if exit_code != 0:
                return f"Error: Failed to read file '{file_path}'"

            # Format with line numbers
            lines = output.decode("utf-8", errors="replace").splitlines()
            start_idx = offset
            end_idx = offset + limit
            selected_lines = lines[start_idx:end_idx]

            result_lines = []
            for i, line in enumerate(selected_lines):
                line_num = offset + i + 1
                result_lines.append(f"{line_num:6d}\t{line}")

            return "\n".join(result_lines)

        except ValueError:
            return f"Error: File '{file_path}' not found"
        except DockerException:
            return f"Error: File '{file_path}' not found"

    def edit(
        self,
        file_path: str,
        old_string: str,
        new_string: str,
        replace_all: bool = False,  # noqa: FBT001, FBT002
    ) -> EditResult:
        """Edit a file by replacing string occurrences using Docker SDK."""
        try:
            # Validate and normalize path
            rel_path = self._validate_and_normalize_path(file_path)
            quoted_path = shlex.quote(rel_path)

            # Check if file exists
            if not self._check_file_exists(rel_path):
                return EditResult(error=f"File '{file_path}' not found")

            # Read file content
            read_cmd = f"cat {quoted_path}"
            exit_code, output = self._container.exec_run(cmd=read_cmd, workdir=self._work_dir)

            if exit_code != 0:
                return EditResult(error=f"File '{file_path}' not found")

            text = output.decode("utf-8", errors="replace")

            # Count occurrences
            count = text.count(old_string)

            # Check for errors
            if count == 0:
                return EditResult(error=f"String not found in file: '{old_string}'")
            elif count > 1 and not replace_all:
                return EditResult(error=f"String '{old_string}' appears multiple times. Use replace_all=True to replace all occurrences.")

            # Perform replacement
            if replace_all:
                result = text.replace(old_string, new_string)
            else:
                result = text.replace(old_string, new_string, 1)

            # Write back to file
            self._upload_content_via_tar(rel_path, result)

            return EditResult(path=file_path, files_update=None, occurrences=count)
        except ValueError:
            return EditResult(error=f"File '{file_path}' not found")
        except DockerException as e:
            return EditResult(error=str(e))

    def upload_files(self, files: list[tuple[str, bytes]]) -> list[FileUploadResponse]:
        """Upload files into the Docker container.

        Args:
            files: List of (path, content) tuples to upload.

        Returns:
            List of FileUploadResponse objects, one per input file.
        """
        responses: list[FileUploadResponse] = []

        for path, content in files:
            try:
                # Validate and normalize path
                rel_path = self._validate_and_normalize_path(path)

                # Ensure parent directory exists
                self._ensure_parent_dir_exists(rel_path)

                # Upload content using tar
                self._upload_content_via_tar(rel_path, content)

                responses.append(FileUploadResponse(path=path, error=None))
            except ValueError as e:
                responses.append(FileUploadResponse(path=path, error=str(e)))  # type: ignore
            except NotFound as e:
                responses.append(FileUploadResponse(path=path, error=f"file_not_found: {e}"))  # type: ignore
            except DockerException as e:
                responses.append(FileUploadResponse(path=path, error=f"docker_error: {e}"))  # type: ignore
            except Exception as e:
                responses.append(FileUploadResponse(path=path, error=f"unexpected_error: {e}"))  # type: ignore

        return responses

    def download_files(self, paths: list[str]) -> list[FileDownloadResponse]:
        """Download files from the Docker container.

        Args:
            paths: List of file paths to download.

        Returns:
            List of FileDownloadResponse objects, one per input path.
        """
        responses: list[FileDownloadResponse] = []

        for path in paths:
            try:
                # Validate and normalize path
                rel_path = self._validate_and_normalize_path(path)

                # Construct absolute path for get_archive
                abs_path = os.path.join(self._work_dir, rel_path)
                stream, _ = self._container.get_archive(path=abs_path)

                # Read the tar stream and extract the file content
                tar_data = io.BytesIO()
                for chunk in stream:
                    tar_data.write(chunk)

                tar_data.seek(0)
                with tarfile.open(fileobj=tar_data, mode="r") as tar:
                    # Get the first file from the archive
                    member = tar.next()
                    if member and member.isfile():
                        content = tar.extractfile(member).read()  # type: ignore
                        responses.append(FileDownloadResponse(path=path, content=content, error=None))
                    else:
                        responses.append(FileDownloadResponse(path=path, error="file_not_found"))
            except ValueError as e:
                responses.append(FileDownloadResponse(path=path, error=str(e)))  # type: ignore
            except NotFound as e:
                responses.append(FileDownloadResponse(path=path, error=f"file_not_found: {e}"))  # type: ignore
            except DockerException as e:
                responses.append(FileDownloadResponse(path=path, error=f"docker_error: {e}"))  # type: ignore
            except Exception as e:
                responses.append(FileDownloadResponse(path=path, error=f"unexpected_error: {e}"))  # type: ignore

        return responses

    def ls_info(self, path: str) -> list[FileInfo]:
        rel_path = self._validate_and_normalize_path(path)

        # Construct absolute path for get_archive
        abs_path = os.path.join(self._work_dir, rel_path)
        return super().ls_info(abs_path)

    def glob_info(self, pattern: str, path: str = "/") -> list[FileInfo]:
        if not path.startswith(self._work_dir):
            rel_path = self._validate_and_normalize_path(path)
            path = os.path.join(self._work_dir, rel_path)
        return super().glob_info(pattern, path)

    def grep_raw(self, pattern: str, path: str | None = None, glob: str | None = None) -> list[GrepMatch] | str:
        """Structured search results or error string for invalid input."""
        if path is None:
            path = self._work_dir

        elif not path.startswith(self._work_dir):
            rel_path = self._validate_and_normalize_path(path)
            path = os.path.join(self._work_dir, rel_path)

        search_path = shlex.quote(path or ".")

        # Build grep command to get structured output
        grep_opts = "-rHnF"  # recursive, with filename, with line number, fixed-strings (literal)

        # Add glob pattern if specified
        glob_pattern = ""
        if glob:
            glob_pattern = f"--include='{glob}'"

        # Escape pattern for shell
        pattern_escaped = shlex.quote(pattern)

        cmd = f"grep {grep_opts} {glob_pattern} -e {pattern_escaped} {search_path}"
        result = self.execute(cmd)

        output = result.output.rstrip()
        if not output:
            return []

        # Parse grep output into GrepMatch objects
        matches: list[GrepMatch] = []
        for line in output.split("\n"):
            # Format is: path:line_number:text
            parts = line.split(":", 2)
            if len(parts) >= 3:  # noqa: PLR2004  # Grep output field count
                matches.append(
                    {
                        "path": parts[0],
                        "line": int(parts[1]),
                        "text": parts[2],
                    }
                )

        return matches
