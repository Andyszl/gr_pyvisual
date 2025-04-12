from pyvis.network import Network
import streamlit as st

def create_graph_visualization(entitys_df, relationship_df, graph_info):
    """
    使用返回的实体和关系数据创建并返回Pyvis网络图
    """
    # 创建网络图对象
    net = Network(height="1200px", width="100%", notebook=True, cdn_resources="in_line")

    # 强制转换 human_readable_id 为整数（核心修复）
    entitys_df['human_readable_id'] = entitys_df['human_readable_id'].astype(int)
    relationship_df['human_readable_id'] = relationship_df['human_readable_id'].astype(int)

    # 创建映射字典（确保 ID 为整数）
    entity_id_map = entitys_df.set_index('human_readable_id').to_dict('index')
    title_to_id = entitys_df.set_index('title')['human_readable_id'].to_dict()  # 新增：通过 title 快速查 ID
    
    relationship_id_map = relationship_df.set_index('human_readable_id').to_dict('index')
    st.subheader("问题关联的社区报告")
    st.dataframe(graph_info)

    # 用于分别保存每次循环的 current_data_entities 和 current_relationships
    all_entities = []
    all_relationships = []
    
    # 假设 df 是包含 data_info 的原始数据框
    for index, row in graph_info.iterrows():
        info = row.get('data_info')  # 假设 data_info 是列名
        if info is None:
            # 处理 info 为 None 的情况，可以选择跳过这一行
            print(f"警告：第 {index} 行的 data_info 为 None，跳过")
            continue
        current_data_entities = []
        current_relationships = []

        # 1. 解析 data_info 中的实体和关系（确保 ID 为整数）
        if 'Entities (' in info:
            entities_str = info.split('Entities (')[1].split(')')[0]
            current_data_entities = [int(e.strip()) for e in entities_str.split(',') if e.strip()]
            #print("current_data_entities: ",current_data_entities)
        if 'Relationships (' in info:
            relationships_str = info.split('Relationships (')[1].split(')')[0]
            current_relationships = [int(r.strip()) for r in relationships_str.split(',') if r.strip()]
            #print("current_relationships:",current_relationships)
        
        
        # 分别保存当前循环的实体和关系
        all_entities.append(current_data_entities)
        all_relationships.append(current_relationships)
        # 2. 收集关系涉及的实体（通过 title 查 ID，确保为整数）
        rel_involved_entities = set()
        for rel_id in current_relationships:
            rel_info = relationship_id_map.get(rel_id, {})
            if not rel_info:
                continue
            source_title = rel_info['source']
            target_title = rel_info['target']
            # 通过 title 查 ID（避免直接从关系表取 ID，确保与 entitys_df 一致）
            source_id = title_to_id.get(source_title)
            target_id = title_to_id.get(target_title)
            if source_id is not None:
                rel_involved_entities.add(source_id)
            if target_id is not None:
                rel_involved_entities.add(target_id)

        # 3. 合并实体并去重（确保所有 ID 为整数）
        all_relevant_entities = set(current_data_entities) | rel_involved_entities

        # 4. 添加节点（显式检查 ID 类型）
        for ent_id in all_relevant_entities:
            if not isinstance(ent_id, (int, str)):
                print(f"警告：非法节点 ID {ent_id}，类型为 {type(ent_id)}，跳过")
                continue
            ent_info = entity_id_map[ent_id]
            node_color = "#FFA500" if ent_id in current_data_entities else "#808080"
            net.add_node(
                ent_id,
                node_size=20,
                label=ent_info['title'],
                title=f"Type: {ent_info['type']}\nDescription: {ent_info['description']}",
                shape='circle',
                color=node_color
            )

        # 5. 添加关系边（确保边的端点 ID 为整数）
        for rel_id in current_relationships:
            rel_info = relationship_id_map.get(rel_id, {})
            if not rel_info:
                continue
            source_title = rel_info['source']
            target_title = rel_info['target']
            source_id = title_to_id.get(source_title)
            target_id = title_to_id.get(target_title)
            if source_id is None or target_id is None:
                print(f"警告：关系 {rel_id} 的源/目标实体不存在，跳过")
                continue
            net.add_edge(
                source_id,
                target_id,
                label=rel_info['description'],
                title=f"Weight: {rel_info['weight']}",
                color='#4285F4',
                width=rel_info['weight'] / 3
            )
    
    all_entities = [num for sublist in all_entities for num in sublist]    
    all_relationships = [num for sublist in all_relationships for num in sublist]
    current_data_entities_df = entitys_df[entitys_df['human_readable_id'].isin(all_entities)]
    current_data_relationships_df = relationship_df[relationship_df['human_readable_id'].isin(all_relationships)]
    
    return current_data_entities_df, current_data_relationships_df,net

def save_graph_to_html(net, filename):
    """
    将网络图保存为HTML文件
    """
    # 生成 HTML 内容
    html_content = net.generate_html()
    # 指定编码为 utf-8 保存文件
    with open(filename, 'w', encoding='utf-8') as f:
        f.write(html_content)
