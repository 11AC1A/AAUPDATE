import json
import os
import tempfile
import unittest
from unittest import mock

import esp32_flasher


HISTORICAL_V240_CONFIG = {
    "firmware_version": "v2.4.0",
    "baud_rate": 921600,
    "chip": "esp32c6",
    "update_log": ["• 提高稳定性，支持ascom修改最大行程限制"],
    "firmware_files": [
        {"address": "0x0", "file": "bootloader.bin", "description": "Bootloader"},
        {"address": "0x8000", "file": "partition-table.bin", "description": "分区表"},
        {"address": "0x10000", "file": "eaf_focuser.bin", "description": "主固件"},
    ],
}


def create_historical_v240_package(folder):
    config_path = os.path.join(folder, "config.json")
    with open(config_path, "w", encoding="utf-8") as config_file:
        json.dump(HISTORICAL_V240_CONFIG, config_file, ensure_ascii=False)
    for firmware in HISTORICAL_V240_CONFIG["firmware_files"]:
        with open(os.path.join(folder, firmware["file"]), "wb") as firmware_file:
            firmware_file.write(b"test firmware")
    return config_path


class ConfigCompatibilityTests(unittest.TestCase):
    def test_historical_v240_config_and_firmware_files(self):
        with tempfile.TemporaryDirectory() as folder:
            config_path = create_historical_v240_package(folder)
            config = esp32_flasher.load_config_file(config_path)

            self.assertEqual(config["firmware_version"], "v2.4.0")
            self.assertEqual(config["chip"], "esp32c6")
            self.assertTrue(config["firmware_files"])
            for firmware in config["firmware_files"]:
                self.assertTrue(os.path.isfile(os.path.join(folder, firmware["file"])))

    def test_flasher_resolves_legacy_files_from_executable_folder_not_working_directory(self):
        with tempfile.TemporaryDirectory() as legacy_dir, tempfile.TemporaryDirectory() as unrelated_working_dir:
            create_historical_v240_package(legacy_dir)
            flasher = esp32_flasher.ESP32Flasher.__new__(esp32_flasher.ESP32Flasher)
            flasher.base_dir = legacy_dir
            flasher.config_error = None

            with mock.patch("os.getcwd", return_value=unrelated_working_dir):
                flasher.load_config()

            self.assertIsNone(flasher.config_error)
            self.assertTrue(flasher.config["firmware_files"])
            self.assertTrue(all(os.path.isfile(flasher.path(item["file"])) for item in flasher.config["firmware_files"]))

    def test_utf8_bom_and_legacy_field_names(self):
        legacy = {
            "version": "v2.0.0",
            "baudrate": 460800,
            "chip_type": "esp32c6",
            "release_notes": "legacy release",
            "files": [{"offset": 0, "filename": "firmware.bin"}],
        }
        with tempfile.TemporaryDirectory() as folder:
            config_path = os.path.join(folder, "config.json")
            with open(config_path, "wb") as config_file:
                config_file.write(b"\xef\xbb\xbf" + json.dumps(legacy).encode("utf-8"))

            config = esp32_flasher.load_config_file(config_path)

        self.assertEqual(config["firmware_version"], "v2.0.0")
        self.assertEqual(config["baud_rate"], 460800)
        self.assertEqual(config["update_log"], ["legacy release"])
        self.assertEqual(config["firmware_files"][0]["address"], "0x0")
        self.assertEqual(config["firmware_files"][0]["file"], "firmware.bin")

    def test_gb18030_config(self):
        legacy = {
            "firmware_version": "旧版",
            "firmware_files": [{"address": "0x10000", "file": "固件.bin"}],
        }
        with tempfile.TemporaryDirectory() as folder:
            config_path = os.path.join(folder, "config.json")
            with open(config_path, "wb") as config_file:
                config_file.write(json.dumps(legacy, ensure_ascii=False).encode("gb18030"))

            config = esp32_flasher.load_config_file(config_path)

        self.assertEqual(config["firmware_version"], "旧版")
        self.assertEqual(config["firmware_files"][0]["file"], "固件.bin")

    def test_packaged_application_uses_executable_directory(self):
        executable = os.path.join("D:\\", "release", "AAHUB_Firmware_Flasher.exe")
        with mock.patch.object(esp32_flasher.sys, "frozen", True, create=True), mock.patch.object(
            esp32_flasher.sys, "executable", executable
        ):
            self.assertEqual(esp32_flasher.application_dir(), os.path.dirname(executable))

    def test_invalid_json_is_reported(self):
        with tempfile.TemporaryDirectory() as folder:
            config_path = os.path.join(folder, "config.json")
            with open(config_path, "w", encoding="utf-8") as config_file:
                config_file.write('{"firmware_files": [}')

            with self.assertRaisesRegex(ValueError, "invalid JSON"):
                esp32_flasher.load_config_file(config_path)

    def test_missing_firmware_guidance_names_files_and_explains_placement(self):
        config = {
            "firmware_files": [
                {"address": "0x0", "file": "bootloader.bin"},
                {"address": "0x10000", "file": "firmware.bin"},
            ]
        }
        with tempfile.TemporaryDirectory() as folder:
            with open(os.path.join(folder, "bootloader.bin"), "wb") as firmware:
                firmware.write(b"present")

            guidance = esp32_flasher.firmware_guidance(config, None, folder, "zh")

        self.assertIn("未检测到完整的固件文件", guidance)
        self.assertIn("firmware.bin", guidance)
        self.assertNotIn("bootloader.bin", guidance)
        self.assertIn("同一文件夹", guidance)
        self.assertIn("重新启动", guidance)

    def test_no_firmware_configuration_guidance_explains_required_files(self):
        guidance = esp32_flasher.firmware_guidance(
            {"firmware_files": []}, None, "D:\\release", "zh"
        )

        self.assertIn("config.json 中没有固件配置", guidance)
        self.assertIn("BIN 固件文件", guidance)

    def test_complete_firmware_package_needs_no_guidance(self):
        with tempfile.TemporaryDirectory() as folder:
            with open(os.path.join(folder, "firmware.bin"), "wb") as firmware:
                firmware.write(b"present")
            config = {"firmware_files": [{"address": "0x0", "file": "firmware.bin"}]}

            guidance = esp32_flasher.firmware_guidance(config, None, folder, "zh")

        self.assertIsNone(guidance)


if __name__ == "__main__":
    unittest.main()
