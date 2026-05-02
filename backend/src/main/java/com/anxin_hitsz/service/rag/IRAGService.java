package com.anxin_hitsz.service.rag;

import com.anxin_hitsz.entity.RAGKnowledgeBase;
import com.baomidou.mybatisplus.extension.service.IService;

import java.util.List;

/**
 * ClassName: IRAGService
 * Package: com.anxin_hitsz.service.rag
 * Description: 知识库服务接口
 *
 * @Author AnXin
 * @Create 2026/5/1
 * @Version 1.0
 */
public interface IRAGService extends IService<RAGKnowledgeBase> {

    /**
     * 获取所有知识库
     */
    List<RAGKnowledgeBase> getList();

    /**
     * 新增知识库
     */
    RAGKnowledgeBase add(RAGKnowledgeBase knowledgeBase);

    /**
     * 更新知识库
     */
    RAGKnowledgeBase update(RAGKnowledgeBase knowledgeBase);

    /**
     * 删除知识库
     */
    void delete(Long ragId);
}
