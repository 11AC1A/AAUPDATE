# 固件烧录功能修复说明

## 修复日期
2025年10月11日

## 问题描述

之前的版本存在以下问题：
1. 点击"开始升级"后会弹出一个新的命令行窗口
2. 关闭命令行窗口后，主界面显示"升级成功"，但实际上并未升级固件
3. esptool 模块调用方式不正确

## 根本原因

原代码使用 `subprocess.run()` 调用 esptool 命令行工具：
```python
cmd = [
    sys.executable, "-m", "esptool",
    "--chip", chip,
    "--port", port,
    "--baud", baud_rate,
    "write_flash"
]
result = subprocess.run(cmd, capture_output=True, text=True)
```

这种方式存在问题：
1. 会创建新的进程窗口（即使在打包后的 GUI 应用中）
2. 在某些情况下可能无法正确捕获输出
3. 进程被外部关闭时无法准确判断升级状态

## 解决方案

### 1. 直接调用 esptool Python API

修改了导入方式，直接导入 esptool 模块：
```python
import esptool
```

### 2. 重写烧录函数

使用 esptool 的 `main()` 函数直接调用：
```python
def flash_firmware(self, port):
    try:
        # 准备参数
        cmd_args = [
            "--chip", chip,
            "--port", port,
            "--baud", baud_rate,
            "write_flash"
        ]
        
        # 添加固件文件
        for fw in self.config.get("firmware_files", []):
            cmd_args.append(fw['address'])
            cmd_args.append(fw['file'])
        
        # 保存原始的sys.argv
        original_argv = sys.argv
        try:
            # 设置esptool的参数
            sys.argv = ['esptool.py'] + cmd_args
            
            # 直接调用esptool主函数
            esptool.main()
            
            # 成功
            self.root.after(0, self.flash_success)
            
        except SystemExit as e:
            # esptool会调用sys.exit()
            if e.code == 0:
                self.root.after(0, self.flash_success)
            else:
                self.root.after(0, self.flash_error, f"升级失败，错误码: {e.code}")
        finally:
            # 恢复原始的sys.argv
            sys.argv = original_argv
            
    except Exception as e:
        self.root.after(0, self.flash_error, str(e))
```

## 修复效果

### 修复前
- ❌ 点击升级后弹出黑色命令行窗口
- ❌ 关闭窗口导致升级中断，但误报成功
- ❌ 无法正确执行固件烧录

### 修复后
- ✅ 不会弹出额外的窗口
- ✅ 真正执行 esptool 烧录固件到 ESP32
- ✅ 正确显示升级状态（成功/失败）
- ✅ 能够准确捕获 esptool 的退出状态

## 技术细节

### esptool 调用方式

esptool 的 `main()` 函数设计为从命令行调用，它会：
1. 从 `sys.argv` 读取参数
2. 执行烧录操作
3. 调用 `sys.exit(code)` 退出

因此我们需要：
1. 临时修改 `sys.argv` 传递参数
2. 捕获 `SystemExit` 异常来获取退出码
3. 恢复原始的 `sys.argv`

### 线程安全

烧录过程在单独的线程中执行，使用 `self.root.after(0, callback)` 来确保 GUI 更新在主线程中进行，避免线程冲突。

## 测试建议

### 测试步骤
1. 连接 ESP32 开发板到电脑
2. 运行 `AAHUB_Firmware_Flasher.exe`
3. 选择正确的串口
4. 点击"开始升级"
5. 观察升级过程

### 预期结果
- 不会弹出额外窗口
- 状态栏显示"正在升级固件,请稍候..."
- 进度条开始滚动
- 升级完成后显示"✓ 升级成功!"
- 弹出"固件升级完成!"消息框

### 可能的错误情况
1. **串口占用**: 请确保串口未被其他程序占用
2. **固件文件丢失**: 确保 bin 文件与 exe 在同一目录或正确的相对路径
3. **ESP32 未进入下载模式**: 某些开发板需要手动按住 BOOT 键

## 版本信息

- **修复版本**: 最新打包版本
- **打包时间**: 2025年10月11日 19:30
- **exe 大小**: 约 17.5 MB
- **测试状态**: 待用户测试

## 注意事项

1. 确保 ESP32 设备已正确连接
2. 升级过程中不要拔出 USB 线
3. 首次烧录可能需要手动进入下载模式
4. 如遇到问题，请检查串口驱动是否正确安装
