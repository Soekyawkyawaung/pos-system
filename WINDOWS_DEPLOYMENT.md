# POS系统Windows部署指南

## 问题说明
在Windows中将Flask应用打包成exe文件后，访问127.0.0.1:5000出现"Not Found"错误，这是因为exe环境下的文件路径处理问题。

## 解决方案

### 方法1：使用提供的打包脚本（推荐）

1. **准备环境**
   ```bash
   # 确保已安装Python 3.7+
   python --version
   
   # 安装必要的包
   pip install flask flask-cors pyinstaller
   ```

2. **运行打包脚本**
   ```bash
   # 在Windows命令提示符中运行
   build_windows.bat
   ```

3. **部署文件**
   - 打包完成后，exe文件在`dist`目录中
   - 将以下文件复制到exe文件同一目录：
     - `index.html`
     - `pos.html`
     - `temp_pos.html`
     - `Profit Calc.html`
     - `static/` (整个目录)
     - `database.py`
     - `pos_system.db`

4. **启动应用**
   - 双击`POS_System.exe`
   - 在浏览器中访问 `http://127.0.0.1:5000`

### 方法2：手动打包

1. **创建spec文件**
   ```bash
   pyi-makespec app.py --onefile --name POS_System
   ```

2. **编辑spec文件**
   在生成的`POS_System.spec`文件中添加数据文件：
   ```python
   datas=[
       ('index.html', '.'),
       ('pos.html', '.'),
       ('temp_pos.html', '.'),
       ('Profit Calc.html', '.'),
       ('static', 'static'),
       ('database.py', '.'),
       ('pos_system.db', '.'),
   ],
   ```

3. **执行打包**
   ```bash
   pyinstaller POS_System.spec
   ```

### 方法3：使用Python脚本打包

```bash
python build_exe.py
```

## 调试方法

如果仍然出现"Not Found"错误，可以使用调试脚本：

```bash
python debug_paths.py
```

这将显示：
- 是否为exe环境
- 应用根目录路径
- 关键文件是否存在
- static目录内容

## 常见问题

### 1. 文件路径问题
**症状**: 访问任何页面都显示"Not Found"
**解决**: 确保所有HTML文件和static目录都在exe文件同一目录下

### 2. 数据库连接问题
**症状**: 应用启动但数据库操作失败
**解决**: 确保`database.py`和`pos_system.db`在正确位置

### 3. 静态文件加载失败
**症状**: 页面显示但样式丢失
**解决**: 确保`static`目录及其内容完整复制

### 4. 端口被占用
**症状**: 应用启动失败
**解决**: 修改`app.py`中的端口号或关闭占用5000端口的程序

## 文件结构要求

打包后的目录结构应该是：
```
POS_System.exe
index.html
pos.html
temp_pos.html
Profit Calc.html
database.py
pos_system.db
static/
  css/
    style.css
```

## 注意事项

1. **防火墙设置**: 确保Windows防火墙允许应用访问网络
2. **杀毒软件**: 某些杀毒软件可能误报exe文件，需要添加白名单
3. **权限问题**: 以管理员身份运行可能解决某些权限问题
4. **路径长度**: Windows路径长度限制可能导致问题，建议使用短路径

## 技术支持

如果遇到问题，请：
1. 运行`debug_paths.py`查看路径信息
2. 检查控制台输出的错误信息
3. 确认所有必要文件都在正确位置 