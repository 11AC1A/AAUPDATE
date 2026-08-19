# AAHUB 固件升级程序 - 打包说明

## 打包环境要求

- Python 3.6 或更高版本
- PyInstaller 打包工具
- 项目所需依赖（esptool, pyserial）

## 快速打包

### 1. 安装打包依赖

```bash
pip install pyinstaller
```

### 2. 执行打包命令

```bash
pyinstaller esp32_flasher.spec
```

打包完成后，可执行文件位于 `dist/AAHUB_Firmware_Flasher.exe`

## 打包配置说明

项目使用 `esp32_flasher.spec` 配置文件进行打包，主要配置项：

### 文件包含
- **主程序**: `esp32_flasher.py`
- **配置文件**: `config.json` 会被自动打包进 exe

### 打包特性
- **单文件模式**: 所有依赖打包成单个 exe 文件
- **无控制台窗口**: `console=False` 隐藏命令行窗口
- **UPX 压缩**: 启用 UPX 压缩减小文件体积

### 隐藏导入
打包配置中包含了以下隐藏导入：
- `serial` - 串口通信
- `serial.tools.list_ports` - 串口设备枚举
- `esptool` - ESP32 烧录工具

## 分发说明

### 必需文件
打包后分发时需要包含以下文件：

```
AAHUB_Firmware_Flasher.exe  # 主程序
config.json                  # 配置文件（exe 会自动释放）
固件文件/
  ├── bootloader.bin
  ├── partition-table.bin
  └── aahub_pro.bin
```

### 配置文件位置
- exe 内置了 config.json，首次运行时会自动释放到当前目录
- 用户可以修改释放出的 config.json 来更新固件版本和更新日志
- 固件文件路径相对于 exe 所在目录

## 自定义打包

### 添加应用图标

1. 准备一个 `.ico` 图标文件
2. 修改 `esp32_flasher.spec` 中的 `icon` 参数：

```python
exe = EXE(
    ...
    icon='icon.ico',  # 设置图标路径
)
```

### 修改输出文件名

修改 `esp32_flasher.spec` 中的 `name` 参数：

```python
exe = EXE(
    ...
    name='您的程序名称',
)
```

### 启用调试模式

如需调试打包后的程序，可以修改以下参数：

```python
exe = EXE(
    ...
    debug=True,      # 启用调试信息
    console=True,    # 显示控制台窗口
)
```

## 常见问题

### 1. 打包后无法找到配置文件

**原因**: config.json 未正确打包或释放路径不对

**解决**: 
- 检查 spec 文件中 `datas=[('config.json', '.')]` 配置
- 确保 config.json 与 esp32_flasher.py 在同一目录

### 2. 打包后无法烧录固件

**原因**: 固件文件路径配置错误

**解决**: 
- 确保固件文件与 exe 在正确的相对路径
- 检查 config.json 中的文件路径配置

### 3. exe 文件过大

**解决**: 
- 确认 UPX 压缩已启用（spec 中 `upx=True`）
- 考虑排除不必要的依赖模块

### 4. 杀毒软件误报

**原因**: PyInstaller 打包的程序可能被杀毒软件误判

**解决**: 
- 对 exe 进行数字签名
- 向杀毒软件厂商提交白名单申请

## 版本信息

- **应用版本**: 通过 config.json 中的 `firmware_version` 字段管理
- **打包工具**: PyInstaller 6.x
- **Python 版本**: 3.13.x

## 技术支持

如有打包相关问题，请联系：
- 官网: www.aaastro.com
- 技术支持: Designed by 11AC1A
