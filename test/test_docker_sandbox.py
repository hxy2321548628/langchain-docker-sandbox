"""Test the DockerSandbox implementation."""

import pytest

from src.langchain_docker_sandbox.sandbox import DockerSandbox


@pytest.fixture
def backend():
    """Create a sandbox instance for testing."""
    return DockerSandbox(container_name="uv-sandbox", work_dir="/workspace")


class TestDockerSandboxId:
    """Test sandbox id property."""

    def test_id(self, backend: DockerSandbox) -> None:
        """Test that id returns the container name."""
        assert backend.id == "uv-sandbox"


class TestDockerSandboxExecute:
    """Test execute method."""

    def test_execute_simple_command(self, backend: DockerSandbox) -> None:
        """Test executing a simple command."""
        result = backend.execute("echo 'Hello from Docker!'")
        assert result.exit_code == 0
        assert "Hello from Docker!" in result.output
        assert result.truncated is False

    def test_execute_with_pwd(self, backend: DockerSandbox) -> None:
        """Test executing command that shows working directory."""
        result = backend.execute("pwd")
        assert result.exit_code == 0
        assert "/workspace" in result.output

    def test_execute_with_ls(self, backend: DockerSandbox) -> None:
        """Test executing ls command."""
        result = backend.execute("ls -la")
        assert result.exit_code == 0

    def test_execute_with_stderr(self, backend: DockerSandbox) -> None:
        """Test executing command that outputs to stderr."""
        result = backend.execute("ls /nonexistent")
        assert result.exit_code != 0

    def test_execute_with_timeout(self, backend: DockerSandbox) -> None:
        """Test executing command with custom timeout."""
        result = backend.execute("echo 'Test with timeout'", timeout=10)
        assert result.exit_code == 0
        assert "Test with timeout" in result.output


class TestDockerSandboxWrite:
    """Test write method."""

    def test_write_simple_file(self, backend: DockerSandbox) -> None:
        """Test writing a simple file."""
        result = backend.write("/test_write.txt", "Hello from Docker sandbox!")
        assert result.path == "/test_write.txt"
        assert result.error is None

        content = backend.read("/test_write.txt")
        assert "Hello from Docker sandbox!" in content

    def test_write_with_subdirectory(self, backend: DockerSandbox) -> None:
        """Test writing a file to a subdirectory."""
        result = backend.write("/subdir/nested.txt", "Nested file content")
        assert result.path == "/subdir/nested.txt"
        assert result.error is None

        content = backend.read("/subdir/nested.txt")
        assert "Nested file content" in content

    def test_write_existing_file(self, backend: DockerSandbox) -> None:
        """Test writing to an existing file should fail."""
        backend.write("/existing.txt", "Initial content")
        result = backend.write("/existing.txt", "New content")
        assert result.error is not None
        assert "already exists" in result.error

    def test_write_empty_file(self, backend: DockerSandbox) -> None:
        """Test writing an empty file."""
        result = backend.write("/empty.txt", "")
        assert result.path == "/empty.txt"
        assert result.error is None

        content = backend.read("/empty.txt")
        assert "" in content


class TestDockerSandboxRead:
    """Test read method."""

    def test_read_simple_file(self, backend: DockerSandbox) -> None:
        """Test reading a simple file."""
        backend.write("/test_read.txt", "Content to read")
        content = backend.read("/test_read.txt")
        assert "Content to read" in content

    def test_read_with_line_numbers(self, backend: DockerSandbox) -> None:
        """Test reading a file with line numbers."""
        backend.write("/multiline.txt", "Line 1\nLine 2\nLine 3\nLine 4")
        content = backend.read("/multiline.txt")
        lines = content.split("\n")
        assert "     1" in lines[0]  # Line 1 with number
        assert "     2" in lines[1]  # Line 2 with number

    def test_read_with_offset(self, backend: DockerSandbox) -> None:
        """Test reading a file with offset."""
        backend.write("/offset.txt", "\n".join([f"Line {i}" for i in range(1, 11)]))
        content = backend.read("/offset.txt", offset=5, limit=2)
        assert "     6" in content  # Should start at line 6 (5 + 1)

    def test_read_with_limit(self, backend: DockerSandbox) -> None:
        """Test reading a file with limit."""
        backend.write("/limit.txt", "\n".join([f"Line {i}" for i in range(1, 11)]))
        content = backend.read("/limit.txt", offset=0, limit=3)
        lines = [line for line in content.split("\n") if line.strip()]
        assert len(lines) == 3

    def test_read_nonexistent_file(self, backend: DockerSandbox) -> None:
        """Test reading a nonexistent file."""
        content = backend.read("/nonexistent.txt")
        assert "Error:" in content
        assert "not found" in content

    def test_read_empty_file(self, backend: DockerSandbox) -> None:
        """Test reading an empty file."""
        backend.write("/empty_read.txt", "")
        content = backend.read("/empty_read.txt")
        assert "" in content


class TestDockerSandboxEdit:
    """Test edit method."""

    def test_edit_single_occurrence(self, backend: DockerSandbox) -> None:
        """Test editing a file with single occurrence replacement."""
        backend.write("/edit_test.txt", "Hello World\nHello Universe\n")
        result = backend.edit("/edit_test.txt", "World", "Galaxy", replace_all=False)
        assert result.path == "/edit_test.txt"
        assert result.error is None
        assert result.occurrences == 1

        content = backend.read("/edit_test.txt")
        assert "Hello Galaxy" in content
        assert "Hello Universe" in content  # Should not be changed

    def test_edit_all_occurrences(self, backend: DockerSandbox) -> None:
        """Test editing a file with replace_all=True."""
        backend.write("/edit_all.txt", "foo bar foo baz foo")
        result = backend.edit("/edit_all.txt", "foo", "qux", replace_all=True)
        assert result.path == "/edit_all.txt"
        assert result.error is None
        assert result.occurrences == 3

        content = backend.read("/edit_all.txt")
        assert "foo" not in content
        assert "qux" in content

    def test_edit_nonexistent_file(self, backend: DockerSandbox) -> None:
        """Test editing a nonexistent file."""
        result = backend.edit("/nonexistent.txt", "old", "new")
        assert result.error is not None
        assert "not found" in result.error

    def test_edit_string_not_found(self, backend: DockerSandbox) -> None:
        """Test editing when the search string is not found."""
        backend.write("/edit_not_found.txt", "Some content")
        result = backend.edit("/edit_not_found.txt", "nonexistent", "replacement")
        assert result.error is not None
        assert "not found" in result.error

    def test_edit_multiple_occurrences_without_replace_all(self, backend: DockerSandbox) -> None:
        """Test editing with multiple occurrences but replace_all=False."""
        backend.write("/edit_multiple.txt", "foo foo foo")
        result = backend.edit("/edit_multiple.txt", "foo", "bar", replace_all=False)
        assert result.error is not None
        assert "multiple times" in result.error


class TestDockerSandboxUploadFiles:
    """Test upload_files method."""

    def test_upload_single_file(self, backend: DockerSandbox) -> None:
        """Test uploading a single file."""
        responses = backend.upload_files([("/upload_test.txt", b"Uploaded content!")])
        assert len(responses) == 1
        assert responses[0].path == "/upload_test.txt"
        assert responses[0].error is None

        content = backend.read("/upload_test.txt")
        assert "Uploaded content!" in content

    def test_upload_multiple_files(self, backend: DockerSandbox) -> None:
        """Test uploading multiple files."""
        responses = backend.upload_files([
            ("/file1.txt", b"Content 1"),
            ("/file2.txt", b"Content 2"),
            ("/subdir/file3.txt", b"Content 3"),
        ])
        assert len(responses) == 3
        for resp in responses:
            assert resp.error is None

        assert "Content 1" in backend.read("/file1.txt")
        assert "Content 2" in backend.read("/file2.txt")
        assert "Content 3" in backend.read("/subdir/file3.txt")

    def test_upload_with_subdirectory(self, backend: DockerSandbox) -> None:
        """Test uploading files to subdirectories."""
        responses = backend.upload_files([
            ("/upload_dir/nested/deep.txt", b"Deep content"),
        ])
        assert responses[0].error is None

        content = backend.read("/upload_dir/nested/deep.txt")
        assert "Deep content" in content

    def test_upload_empty_content(self, backend: DockerSandbox) -> None:
        """Test uploading a file with empty content."""
        responses = backend.upload_files([("/empty_upload.txt", b"")])
        assert responses[0].error is None

        content = backend.read("/empty_upload.txt")
        assert "" in content


class TestDockerSandboxDownloadFiles:
    """Test download_files method."""

    def test_download_single_file(self, backend: DockerSandbox) -> None:
        """Test downloading a single file."""
        backend.write("/download_test.txt", "Content to download")
        responses = backend.download_files(["/download_test.txt"])
        assert len(responses) == 1
        assert responses[0].path == "/download_test.txt"
        assert responses[0].error is None
        assert responses[0].content == b"Content to download"

    def test_download_multiple_files(self, backend: DockerSandbox) -> None:
        """Test downloading multiple files."""
        backend.write("/dl1.txt", "File 1")
        backend.write("/dl2.txt", "File 2")
        backend.write("/dl3.txt", "File 3")

        responses = backend.download_files(["/dl1.txt", "/dl2.txt", "/dl3.txt"])
        assert len(responses) == 3
        for resp in responses:
            assert resp.error is None
            assert resp.content is not None

    def test_download_nonexistent_file(self, backend: DockerSandbox) -> None:
        """Test downloading a nonexistent file."""
        responses = backend.download_files(["/nonexistent_download.txt"])
        assert len(responses) == 1
        assert responses[0].error is not None
        assert "not_found" in responses[0].error

    def test_download_empty_file(self, backend: DockerSandbox) -> None:
        """Test downloading an empty file."""
        backend.write("/empty_download.txt", "")
        responses = backend.download_files(["/empty_download.txt"])
        assert responses[0].error is None
        assert responses[0].content == b""


class TestDockerSandboxLsInfo:
    """Test ls_info method."""

    def test_ls_info_root(self, backend: DockerSandbox) -> None:
        """Test listing files in root directory."""
        backend.write("/ls_test1.txt", "test1")
        backend.write("/ls_test2.txt", "test2")

        files = backend.ls_info("/")
        assert len(files) > 0

        file_names = [f["path"] for f in files]
        assert f"{backend._work_dir}/./ls_test1.txt" in file_names or "ls_test1.txt" in file_names
        assert f"{backend._work_dir}/./ls_test2.txt" in file_names or "ls_test2.txt" in file_names

    def test_ls_info_subdirectory(self, backend: DockerSandbox) -> None:
        """Test listing files in a subdirectory."""
        backend.write("/ls_dir/file1.txt", "content1")
        backend.write("/ls_dir/file2.txt", "content2")

        files = backend.ls_info("/ls_dir")
        assert len(files) >= 2

        file_names = [f["path"] for f in files]
        assert f"{backend._work_dir}/ls_dir/file1.txt" in file_names or "/ls_dir/file1.txt" in file_names
        assert f"{backend._work_dir}/ls_dir/file2.txt" in file_names or "/ls_dir/file2.txt" in file_names


class TestDockerSandboxGlobInfo:
    """Test glob_info method."""

    def test_glob_info_pattern(self, backend: DockerSandbox) -> None:
        """Test globbing files with a pattern."""
        backend.write("/glob_test1.txt", "test1")
        backend.write("/glob_test2.txt", "test2")
        backend.write("/glob_other.txt", "other")

        files = backend.glob_info("glob_test*.txt")
        assert len(files) >= 2

        file_names = [f["path"] for f in files]
        assert any("glob_test1" in name for name in file_names)
        assert any("glob_test2" in name for name in file_names)


class TestDockerSandboxGrepRaw:
    """Test grep_raw method."""

    def test_grep_simple_pattern(self, backend: DockerSandbox) -> None:
        """Test grepping for a simple pattern."""
        backend.write("/grep_test.txt", "Hello World\nHello Universe\nGoodbye World")

        results = backend.grep_raw("World")
        assert len(results) >= 2
        assert any("Hello World" in r["text"] for r in results) # type: ignore
        assert any("Goodbye World" in r['text'] for r in results) # type: ignore


class TestDockerSandboxIntegration:
    """Integration tests for multiple operations."""

    def test_write_read_edit_cycle(self, backend: DockerSandbox) -> None:
        """Test complete write -> read -> edit cycle."""
        result = backend.write("/cycle.txt", "Initial content")
        assert result.error is None

        content = backend.read("/cycle.txt")
        assert "Initial content" in content

        edit_result = backend.edit("/cycle.txt", "Initial", "Updated")
        assert edit_result.error is None

        updated = backend.read("/cycle.txt")
        assert "Updated content" in updated

    def test_upload_download_cycle(self, backend: DockerSandbox) -> None:
        """Test complete upload -> download cycle."""
        original_content = b"Upload download test content"

        upload_resp = backend.upload_files([("/cycle_file.txt", original_content)])
        assert upload_resp[0].error is None

        download_resp = backend.download_files(["/cycle_file.txt"])
        assert download_resp[0].error is None
        assert download_resp[0].content == original_content

    def test_complex_workflow(self, backend: DockerSandbox) -> None:
        """Test a complex workflow with multiple operations."""
        # Create directory structure
        backend.write("/project/main.py", "print('Hello')")
        backend.write("/project/utils.py", "def helper(): pass")
        backend.write("/project/README.md", "# Project\n\nDescription")

        # List files
        files = backend.ls_info("/project")
        assert len(files) >= 3

        # Update file
        backend.edit("/project/main.py", "print('Hello')", "print('World')")

        # Verify update
        content = backend.read("/project/main.py")
        assert "World" in content

        # Upload additional file
        backend.upload_files([("/project/extra.txt", b"Extra content")])

        # Download all files
        paths = [f["path"] for f in files] + ["/project/extra.txt"]
        responses = backend.download_files(paths)
        assert all(resp.error is None for resp in responses)
