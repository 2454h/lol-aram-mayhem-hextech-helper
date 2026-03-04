# 封装审核报告（Windows）

## 审核范围
- 打包配置正确性
- 规则数据一致性
- 自动化验证可复现性
- 产物可交付性

## 发现与修复
1. `build_windows.spec` 在 PyInstaller 环境中使用 `__file__` 导致构建失败  
   - 处理：改为 `Path(globals().get("SPECPATH", ".")).resolve()`
2. `conversion_rules.json` 的部分 `trigger_augment` 方向与测试不一致  
   - 处理：修正触发方向，保证“探险家=魔法转物理”“放逐之刃=物理转魔法”
3. 封装后 OCR 动态模块加载失败（`ch_ppocr_v3_det.TextDetector`）  
   - 处理：
     - 在 `main.py` 增加 RapidOCR 动态模块别名注入
     - 在 `build_windows.spec` 增加 RapidOCR 动态子模块 hiddenimports

## 验证记录
- 单元测试：`python -m pytest -q` → `7 passed`
- 封装构建：`pyinstaller build_windows.spec --noconfirm --clean` → 成功
- OCR 初始化：`python -c "from main import DataManager, GameAnalyzer; ..."` → `ocr-init-ok`
- 安装器编译器检测：当前环境 `Inno Setup` 未安装，安装包编译步骤未在本机执行

## 产物状态
- 目录版产物存在：`dist/大乱斗海克斯助手/大乱斗海克斯助手.exe`
- 当前目录版体积约：220MB（已剔除 torch/scipy 等重依赖）

## 专业复核清单
- 在审核机安装 Inno Setup 6 后执行：
  - `powershell -ExecutionPolicy Bypass -File .\scripts\build_windows_release.ps1 -Version x.y.z`
- 在干净 Windows 机器执行以下验收：
  - 安装 Setup 包成功
  - 首次启动出现 UAC 提权
  - 选择英雄流程正常
  - F6 OCR 识别正常
  - F8 重置流程正常
  - 无 `TextDetector` 相关异常
