# Esptool Stub Flasher 文件缺失问题修复

## 问题描述
打包后的 exe 运行时报错：
```
stub flasher json file for esp32 not found
```

## 问题原因
PyInstaller 在打包时默认不会自动收集 esptool 包中的数据文件，这些数据文件包括：
- stub flasher JSON 文件
- 各种芯片型号的 stub 二进制文件
- 其他必需的资源文件

这些文件对于 esptool 正常工作是必需的，缺失会导致无法烧录固件。

## 解决方案

### 修改 esp32_flasher.spec 文件

在 spec 文件开头添加导入和数据收集：

```python
import os
from PyInstaller.utils.hooks import collect_data_files

# 收集 esptool 的数据文件（包括 stub flasher JSON 文件）
esptool_datas = collect_data_files('esptool')
```

然后在 Analysis 的 datas 参数中添加收集到的文件：

```python
a = Analysis(
    ['esp32_flasher.py'],
    pathex=[],
    binaries=[],
    datas=[('config.json', '.')] + esptool_datas,  # 包含配置文件和 esptool 数据文件
    ...
)
```

## 技术说明

### collect_data_files 函数
`collect_data_files('esptool')` 会自动查找并收集 esptool 包中的所有数据文件：
- 搜索 esptool 安装目录
- 识别所有非 .py 的数据文件
- 保持原始的目录结构
- 返回 PyInstaller 可用的 (source, dest) 元组列表

### 包含的文件类型
- `.json` - 芯片配置和 stub 定义文件
- `.bin` - 预编译的 stub flasher 二进制文件
- 其他资源文件

## 验证修复

### 1. 重新打包
```bash
pyinstaller --clean esp32_flasher.spec
```

### 2. 测试运行
- 运行 `AAHUB_Firmware_Flasher.exe`
- 选择串口
- 点击"开始升级"
- 不应再出现 "stub flasher json file not found" 错误

### 3. 预期行为
- esptool 正常初始化
- 成功连接 ESP32
- 正常烧录固件

## 打包信息

- **打包时间**: 2025年10月11日
- **PyInstaller 版本**: 6.16.0
- **esptool 版本**: 4.6+
- **修复状态**: ✅ 已修复

## 注意事项

1. **文件大小增加**: 包含 esptool 数据文件后，exe 文件会略微增大（增加约 100-200 KB）
2. **首次运行**: 首次运行时 esptool 会从打包的资源中提取所需文件到临时目录
3. **芯片支持**: 现在支持所有 esptool 支持的芯片型号（ESP32, ESP32-S2, ESP32-S3, ESP32-C3 等）

## 相关问题

### 如果仍然出错
1. 确认使用的是最新打包的 exe
2. 检查 build 目录已清理（使用 --clean 参数）
3. 验证 esptool 包已正确安装在虚拟环境中

### 调试方法
如需调试，可以暂时启用控制台窗口：
```python
# 在 esp32_flasher.spec 中修改
exe = EXE(
    ...
    console=True,  # 临时启用以查看错误信息
)
```

## 总结

通过使用 PyInstaller 的 `collect_data_files` 工具函数，我们确保了 esptool 的所有必需数据文件都被正确打包到最终的 exe 中，从而解决了 stub flasher JSON 文件缺失的问题。
