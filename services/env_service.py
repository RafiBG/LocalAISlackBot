from pathlib import Path


class EnvService:
    def __init__(self, path: str = ".env"):
        self.path = Path(path)

    def read_raw_lines(self):
        if not self.path.exists():
            return []
        with open(self.path, "r", encoding="utf-8") as f:
            return f.readlines()

    def read(self) -> dict:
        data = {}
        lines = self.read_raw_lines()

        for line in lines:
            stripped = line.strip()

            if not stripped or stripped.startswith("#"):
                continue

            if "=" not in stripped:
                continue

            key, value = stripped.split("=", 1)
            data[key] = value

        return data

    def write_selected(self, updates: dict):
        lines = self.read_raw_lines()
        new_lines = []

        for line in lines:
            stripped = line.strip()

            if not stripped or stripped.startswith("#") or "=" not in stripped:
                new_lines.append(line)
                continue

            key, _ = stripped.split("=", 1)

            if key in updates:
                new_lines.append(f"{key}={updates[key]}\n")
            else:
                new_lines.append(line)

        with open(self.path, "w", encoding="utf-8") as f:
            f.writelines(new_lines)
