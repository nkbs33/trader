# A股量化交易系统

这是一个基于Python的A股量化交易分析系统，提供股票数据获取、可视化分析和策略筛选功能。

## 功能特性

- **数据获取**: 通过akshare库获取A股历史数据
- **可视化分析**: 使用Plotly创建交互式K线图，包含KDJ指标和成交量
- **策略筛选**: 基于KDJ指标筛选超卖股票
- **Web界面**: 使用Dash创建交互式Web应用
- **本地存储**: SQLite数据库存储股票数据

## 系统架构

- `app.py`: Dash Web应用，提供交互式股票查询界面
- `plot.py`: 股票图表生成，包含K线图、成交量和KDJ指标
- `db_init.py`: 股票数据初始化和批量下载
- `picker.py`: 股票筛选器，基于KDJ指标筛选股票
- `db_util.py`: 数据库工具类，提供数据访问功能

## 安装说明

1. 创建虚拟环境并安装依赖：
   ```bash
   python -m venv ak_env
   source ak_env/bin/activate  # 在Windows上使用: ak_env\Scripts\activate
   pip install akshare plotly dash pandas
   ```

2. 或者直接运行命令文件：
   ```bash
   source commands
   ```

## 使用方法

### 1. 数据初始化
```bash
python db_init.py --start 20200101 --end 20251231 --sleep 0.3
```
参数说明：
- `--limit`: 限制获取股票数量（用于测试）
- `--start`: 开始日期（格式：YYYYMMDD）
- `--end`: 结束日期（格式：YYYYMMDD）
- `--sleep`: 请求间隔时间（秒）

### 2. 启动Web界面
```bash
python app.py
```
访问 `http://127.0.0.1:8050` 查看交互式股票分析界面

### 3. 股票筛选
```bash
python picker.py
```
根据KDJ指标筛选J值低于12的超卖股票，并将结果保存到result目录

## 图表功能

- **主图**: K线图显示开盘价、最高价、最低价、收盘价
- **移动平均线**: 10日移动平均线
- **成交量**: 柱状图显示成交量，红色表示上涨，绿色表示下跌
- **KDJ指标**: 显示K、D、J线，以及超买超卖区域线

## 技术栈

- Python 3.x
- akshare: A股数据获取
- Dash: Web界面框架
- Plotly: 交互式图表
- Pandas: 数据处理
- SQLite: 本地数据库

## 项目结构

```
trader/
├── app.py          # Web应用主入口
├── plot.py         # 图表生成模块
├── db_init.py      # 数据库初始化
├── picker.py       # 股票筛选器
├── db_util.py      # 数据库工具类
├── commands        # 安装命令脚本
├── result/         # 筛选结果输出目录
└── ak_env/         # Python虚拟环境
```

## 注意事项

- 本系统仅供学习和研究使用，不构成投资建议
- 数据获取频率受API限制，请合理设置sleep参数
- 建议在虚拟环境中运行以避免依赖冲突

## 扩展功能

- 支持多种技术指标计算
- 历史查询记录功能
- 可自定义筛选条件
- 响应式Web界面设计