# Origin Pro 2024 MCP Server

为 AI Agent（Claude Code、Cursor、Cherry Studio 等）提供 Origin Pro 2024 自动化控制能力的 MCP 服务。

## 前置要求

- **Windows 系统**（Origin Pro 仅支持 Windows）
- **Origin Pro 2024**（已安装并激活许可证）
- **Python >= 3.10**
- **uv**（推荐）或 npm

## 安装

无需手动安装，MCP 客户端会通过 `uvx` 自动拉取并运行。

如需本地开发：

```bash
git clone https://github.com/noc228076/origin-pro-mcp.git
cd origin-pro-mcp
uv pip install -e .
```

## 配置 MCP 客户端

### Claude Code

在 MCP 配置文件（`.mcp.json`）中添加：

```json
{
  "origin-pro": {
    "type": "stdio",
    "command": "uvx",
    "args": ["origin-pro-mcp"]
  }
}
```

### Cursor

在 `.cursor/mcp.json` 中添加（Cursor 使用 `mcpServers` 包裹格式）：

```json
{
  "mcpServers": {
    "origin-pro": {
      "type": "stdio",
      "command": "uvx",
      "args": ["origin-pro-mcp"]
    }
  }
}
```

### Cherry Studio

在 Cherry Studio 设置中添加 MCP 服务器，传输类型选择 **stdio**：

- 命令：`uvx`
- 参数：`origin-pro-mcp`

### 从源码运行（本地开发）

如果你 clone 了本仓库，也可以指定本地目录：

```json
{
  "origin-pro": {
    "type": "stdio",
    "command": "uv",
    "args": ["--directory", "/path/to/origin-pro-mcp", "run", "origin-pro-mcp"]
  }
}
```

## 提供的工具（共 30 个）

### 连接管理
| 工具 | 说明 |
|------|------|
| `origin_connect` | 连接到 Origin Pro 实例 |
| `origin_info` | 获取 Origin 版本和路径信息 |

### 项目管理
| 工具 | 说明 |
|------|------|
| `project_new` | 新建空白项目 |
| `project_open` | 打开 .opju/.opj 项目文件 |
| `project_save` | 保存当前项目 |

### 工作表/数据操作
| 工具 | 说明 |
|------|------|
| `workbook_create` | 创建新工作簿 |
| `worksheet_create` | 创建新工作表 |
| `worksheet_set_data` | 向列写入数据 |
| `worksheet_get_data` | 从列读取数据 |
| `worksheet_set_labels` | 设置列标签（名称/单位/注释） |
| `worksheet_list` | 列出所有工作簿和工作表 |
| `import_csv` | 导入 CSV/文本文件 |
| `import_excel` | 导入 Excel 文件 |

### 图表创建与样式
| 工具 | 说明 |
|------|------|
| `graph_create` | 创建图表（折线/散点/柱状/等高线/3D 等 20 种类型） |
| `graph_add_plot` | 向图表添加数据绘图 |
| `graph_set_axis_titles` | 设置坐标轴标题 |
| `graph_set_axis_range` | 设置坐标轴范围 |
| `graph_set_plot_style` | 设置绘图样式（颜色/线宽/符号等） |
| `graph_set_title` | 设置图表标题 |
| `graph_rescale` | 自动缩放图表 |
| `graph_list` | 列出所有图表 |
| `graph_export` | 导出图表为图片（PNG/PDF/SVG/EMF 等） |
| `graph_export_all` | 批量导出所有图表 |

### 数据分析
| 工具 | 说明 |
|------|------|
| `analysis_linear_fit` | 线性回归拟合 |
| `analysis_polynomial_fit` | 多项式拟合 |
| `analysis_nonlinear_fit` | 非线性拟合（Gauss/Lorentz/Voigt 等） |
| `analysis_statistics` | 描述性统计 |
| `analysis_fft` | 快速傅里叶变换 |
| `analysis_peak_find` | 峰值查找 |
| `analysis_smooth` | 数据平滑 |
| `analysis_baseline` | 基线校正 |
| `analysis_interpolate` | 数据插值 |

### 高级
| 工具 | 说明 |
|------|------|
| `labtalk_execute` | 执行任意 LabTalk 脚本（万能后门） |
| `page_delete` | 删除页面 |

## 使用示例

Agent 调用流程示例：

```
1. origin_connect          → 连接到 Origin Pro
2. import_csv("data.csv")  → 导入数据
3. graph_create("scatter")  → 创建散点图
4. graph_add_plot(...)      → 添加数据到图表
5. graph_set_axis_titles(x_title="Time (s)", y_title="Voltage (V)")
6. analysis_linear_fit(...) → 线性拟合
7. graph_export("fig.png")  → 导出图表
8. project_save("out.opju") → 保存项目
```

## 架构

```
AI Agent (Claude / Cursor / Cherry Studio)
    │  stdio (MCP protocol)
    ▼
MCP Server (Python, 本服务)
    │  originpro package → COM automation
    ▼
Origin Pro 2024 (GUI 实时可见)
```

## 许可证

MIT
