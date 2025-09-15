"""CUE/BIN file format validator for PlayStation platforms."""

from pathlib import Path


class CueBinValidator:
    """Handles validation of CUE/BIN multi-file ROM formats."""

    def validate_cue_bin(self, cue_path: Path) -> bool:
        """Validate a .cue file and its associated .bin files."""
        if not cue_path.exists() or cue_path.suffix.lower() != ".cue":
            return False

        try:
            with open(cue_path, encoding="utf-8", errors="ignore") as f:
                content = f.read()

            # Look for FILE entries in the .cue file
            bin_files = self._parse_cue_file_references(content, cue_path.parent)

            # Check if all referenced .bin files exist
            return len(bin_files) > 0 and all(bin_file.exists() for bin_file in bin_files)

        except (OSError, UnicodeDecodeError):
            return False

    def get_related_files(self, primary_file: Path) -> list[Path]:
        """Get all files that are part of this multi-file ROM."""
        extension = primary_file.suffix.lower()
        related_files = [primary_file]

        if extension == ".cue":
            # For .cue files, find associated .bin files
            try:
                with open(primary_file, encoding="utf-8", errors="ignore") as f:
                    content = f.read()

                bin_files = self._parse_cue_file_references(content, primary_file.parent)
                related_files.extend(bin_files)

            except (OSError, UnicodeDecodeError):
                pass

        elif extension == ".bin":
            # For .bin files, find associated .cue file
            cue_path = primary_file.with_suffix(".cue")
            if cue_path.exists():
                related_files.append(cue_path)

        return related_files

    def _parse_cue_file_references(self, cue_content: str, cue_dir: Path) -> list[Path]:
        """Parse .cue file content to find referenced files."""
        bin_files = []
        lines = cue_content.split("\n")

        for line in lines:
            line = line.strip()
            if line.upper().startswith("FILE") and (".BIN" in line.upper() or ".bin" in line):
                # Extract filename from FILE line
                # Format: FILE "filename.bin" BINARY
                parts = line.split('"')
                if len(parts) >= 3:
                    bin_filename = parts[1]
                    bin_path = cue_dir / bin_filename
                    bin_files.append(bin_path)
                else:
                    # Try space-separated format: FILE filename.bin BINARY
                    parts = line.split()
                    if len(parts) >= 2:
                        bin_filename = parts[1]
                        if bin_filename.startswith('"') and bin_filename.endswith('"'):
                            bin_filename = bin_filename[1:-1]
                        bin_path = cue_dir / bin_filename
                        bin_files.append(bin_path)

        return bin_files

    def is_multi_file_primary(self, file_path: Path) -> bool:
        """Check if file is a primary file in a multi-file set."""
        extension = file_path.suffix.lower()

        # .cue files are primary files for CUE/BIN sets
        if extension == ".cue":
            return self.validate_cue_bin(file_path)

        return False

    def find_multi_file_primary(self, file_path: Path) -> Path | None:
        """Find the primary file for a multi-file ROM set."""
        extension = file_path.suffix.lower()

        if extension == ".bin":
            # Look for associated .cue file
            cue_path = file_path.with_suffix(".cue")
            if cue_path.exists() and self.validate_cue_bin(cue_path):
                return cue_path

        elif extension == ".cue":
            # .cue files are primary themselves
            if self.validate_cue_bin(file_path):
                return file_path

        return None
