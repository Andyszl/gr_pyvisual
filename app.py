import pandas as pd
import asyncio
import streamlit as st
from graphrag_query import query_graph
from graph_visualization import create_graph_visualization, save_graph_to_html
import base64

# Streamlit 页面配置
st.set_page_config(page_title="Graph Visualization", layout="wide")

# 页面标题
st.title("graphRAG查询系统")

# 输入框：让用户输入查询
user_query = st.text_input("输入查询内容:", "介绍下苏轼")
# 提供下载链接，点击后页面不刷新
def get_binary_file_downloader_html(bin_file, file_label='File'):
    with open(bin_file, 'rb') as f:
        data = f.read()
    bin_str = base64.b64encode(data).decode()
    href = f'<a href="data:application/octet-stream;base64,{bin_str}" download="{file_label}.html">Download {file_label} as HTML</a>'
    return href

# 查询按钮
if st.button('查询'):
    with st.spinner('正在查询...'):
        # 获取实体数据和关系数据
        graph_info_df,entitys_df, relationship_df, result_text = asyncio.run(query_graph(user_query))
        st.write('查询结果:')
        st.markdown(
            f"""
            <div style="border: 1px solid #ccc; padding: 15px; border-radius: 5px; margin: 10px 0;">
                {result_text}
            </div>
            """,
            unsafe_allow_html=True
        )
        

        # 创建图形并保存为 HTML
        current_data_entities_df, current_data_relationships_df, net = create_graph_visualization(entitys_df, relationship_df, graph_info_df)
        graph_html_path = './data/graph.html'  # 存储路径
        
        current_data_entities_df = current_data_entities_df[['human_readable_id', 'title', 'description']].rename(columns={'human_readable_id': 'ID', 'title': '名称', 'description': '描述'})
        current_data_relationships_df = current_data_relationships_df[['human_readable_id',"source"	,"target",  'description']].rename(columns={'human_readable_id': 'ID',  'description': '描述'})
        st.subheader("解析的实体和关系")
        st.subheader("实体")
        st.dataframe(current_data_entities_df)
        st.subheader("关系")
        st.dataframe(current_data_relationships_df)
        
        # 保存 HTML
        save_graph_to_html(net, graph_html_path)
        
        # 显示图形链接
        st.subheader("可视化展示")
        #st.markdown(f"Click the link to view the graph: [View Graph]({graph_html_path})")
        # 在网页中展示 HTML 内容
        with open(graph_html_path, 'r', encoding='utf-8') as f:
            html_content = f.read()
            st.components.v1.html(html_content, height=600)  # 可以根据需要调整高度
        
        # 提供下载链接
        st.download_button(label="Download Graph as HTML", data=open(graph_html_path, 'rb'), file_name="graph.html", mime="application/octet-stream")
        st.markdown(get_binary_file_downloader_html(graph_html_path, 'graph'), unsafe_allow_html=True)
