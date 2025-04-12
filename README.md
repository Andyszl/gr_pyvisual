# 知识图谱问答系统

## 项目简介

该项目使用Streamlit构建了一个Web应用，用户可以输入自然语言查询，系统通过GraphRAG的`global`查询方法处理查询，并使用Pyvis可视化相关的知识图谱。

## 项目结构

- `app.py`：Streamlit应用主文件。
- `graphrag_query.py`：封装GraphRAG查询功能的模块。
- `graph_visualization.py`：处理图形可视化的模块。
- `requirements.txt`：项目依赖。
- `data/`：存放节点和边数据的目录。

## 使用方法

1. 安装依赖：

   ```bash
   pip install -r requirements.txt
