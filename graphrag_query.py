import os
import re
import pandas as pd
from io import StringIO
import streamlit as st

import tiktoken
from dotenv import load_dotenv
from configparser import ConfigParser
from graphrag.query.indexer_adapters import (
    read_indexer_communities,
    read_indexer_entities,
    read_indexer_reports,
)
from graphrag.query.llm.oai.chat_openai import ChatOpenAI
from graphrag.query.llm.oai.typing import OpenaiApiType
from graphrag.query.structured_search.global_search.community_context import (
    GlobalCommunityContext,
)
from graphrag.query.structured_search.global_search.search import GlobalSearch

# 自定义处理关系的函数
def process_relationships(relationship_df):
    relationships = []
    for _, row in relationship_df.iterrows():
        relationships.append({
            'source': row['source'],
            'target': row['target'],
            'relation': row.get('relation', 'default_relation')  # 如果 'relation' 列缺失，使用默认值
        })
    return relationships

# 加载环境变量
load_dotenv()
# 打印当前工作目录
current_dir = os.getcwd()
#st.write(f"当前工作目录: {current_dir}")


# 读取配置文件
config = ConfigParser()
config_file_path = 'config.ini'
config.read(config_file_path)

# if os.path.exists(config_file_path):
#     config.read(config_file_path)
#     st.write("成功读取配置文件")
# else:
#     st.write(f"未找到配置文件: {config_file_path}")
# 获取数据文件夹路径，默认为'./data'
data_folder = config.get('paths', 'data_folder', fallback='data')

# 查询引擎的配置
context_builder_params = {
    "use_community_summary": config.getboolean('context_builder_params', 'use_community_summary'),
    "shuffle_data": config.getboolean('context_builder_params', 'shuffle_data'),
    "include_community_rank": config.getboolean('context_builder_params', 'include_community_rank'),
    "min_community_rank": config.getint('context_builder_params', 'min_community_rank'),
    "community_rank_name": config.get('context_builder_params', 'community_rank_name'),
    "include_community_weight": config.getboolean('context_builder_params', 'include_community_weight'),
    "community_weight_name": config.get('context_builder_params', 'community_weight_name'),
    "normalize_community_weight": config.getboolean('context_builder_params', 'normalize_community_weight'),
    "max_tokens": config.getint('context_builder_params', 'max_tokens'),
    "context_name": config.get('context_builder_params', 'context_name'),
}

map_llm_params = {
    "max_tokens": config.getint('map_llm_params', 'max_tokens'),
    "temperature": config.getfloat('map_llm_params', 'temperature'),
    "response_format": config.get('map_llm_params', 'response_format'),
}

reduce_llm_params = {
    "max_tokens": config.getint('reduce_llm_params', 'max_tokens'),
    "temperature": config.getfloat('reduce_llm_params', 'temperature'),
}

# 初始化OpenAI LLM
llm = ChatOpenAI(
    api_key=os.getenv("openai_api_key", None),
    model="deepseek-chat",
    api_base=os.getenv("base_url", None),
    api_type=OpenaiApiType.OpenAI,
    max_retries=20,
)

token_encoder = tiktoken.get_encoding("cl100k_base")

# 读取数据
nodes_df = pd.read_parquet(f"./{data_folder}/output/create_final_nodes.parquet")
entitys_df = pd.read_parquet(f"./{data_folder}/output/create_final_entities.parquet")
entities = read_indexer_entities(nodes_df, entitys_df, None)

relationship_df = pd.read_parquet(f"./{data_folder}/output/create_final_relationships.parquet")
relationships = process_relationships(relationship_df)

report_df = pd.read_parquet(f"./{data_folder}/output/create_final_community_reports.parquet")
reports = read_indexer_reports(report_df, nodes_df, None)

community_df = pd.read_parquet(f"./{data_folder}/output/create_final_communities.parquet")
communities = read_indexer_communities(community_df, nodes_df, report_df)

# 构建上下文
context_builder = GlobalCommunityContext(
    community_reports=reports,
    communities=communities,
    entities=entities,
    token_encoder=token_encoder,
)

# 初始化查询引擎
search_engine = GlobalSearch(
    llm=llm,
    context_builder=context_builder,
    token_encoder=token_encoder,
    max_data_tokens=12_000,
    map_llm_params=map_llm_params,
    reduce_llm_params=reduce_llm_params,
    allow_general_knowledge=False,
    json_mode=True,
    context_builder_params=context_builder_params,
    concurrent_coroutines=32,
    response_type="multiple paragraphs",
)


async def query_graph(query):
    """
    使用GlobalSearch执行查询，并返回包含实体和关系的数据
    """
    result = await search_engine.asearch(query)

    # 获取结果中的 context_text（包含多个报告）
    context_text = result.context_text

    # 将列表中的元素合并为一个字符串
    text = ''.join(result.context_text)

    # 使用 StringIO 将字符串转换为文件对象
    file = StringIO(text)

    # 读取数据并创建 DataFrame
    df = pd.read_csv(file, sep='|')
    
    # 定义正则表达式匹配 [Data: ...] 内容
    pattern = r'\[Data: (.*?)\]'

    # 提取并新增列
    df['data_info'] = df['content'].apply(lambda x: re.search(pattern, x).group() if re.search(pattern, x) else None)

    return df,entitys_df, relationship_df, result.response
