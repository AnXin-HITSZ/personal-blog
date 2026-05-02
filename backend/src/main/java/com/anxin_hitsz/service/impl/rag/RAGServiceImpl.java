package com.anxin_hitsz.service.impl.rag;

import com.anxin_hitsz.entity.RAGKnowledgeBase;
import com.anxin_hitsz.mapper.rag.RAGMapper;
import com.anxin_hitsz.service.rag.IRAGService;
import com.baomidou.mybatisplus.core.conditions.query.QueryWrapper;
import com.baomidou.mybatisplus.extension.service.impl.ServiceImpl;
import org.springframework.stereotype.Service;

import java.time.LocalDateTime;
import java.util.List;

/**
 * ClassName: RAGServiceImpl
 * Package: com.anxin_hitsz.service.impl.rag
 * Description: 知识库服务实现
 *
 * @Author AnXin
 * @Create 2026/5/1
 * @Version 1.0
 */
@Service
public class RAGServiceImpl extends ServiceImpl<RAGMapper, RAGKnowledgeBase> implements IRAGService {

    @Override
    public List<RAGKnowledgeBase> getList() {
        QueryWrapper<RAGKnowledgeBase> wrapper = new QueryWrapper<>();
        wrapper.orderByDesc("created_at");
        return list(wrapper);
    }

    @Override
    public RAGKnowledgeBase add(RAGKnowledgeBase knowledgeBase) {
        knowledgeBase.setCreatedAt(LocalDateTime.now());
        knowledgeBase.setUpdatedAt(LocalDateTime.now());
        if (knowledgeBase.getStatus() == null) {
            knowledgeBase.setStatus(0);
        }
        save(knowledgeBase);
        return knowledgeBase;
    }

    @Override
    public RAGKnowledgeBase update(RAGKnowledgeBase knowledgeBase) {
        knowledgeBase.setUpdatedAt(LocalDateTime.now());
        updateById(knowledgeBase);
        return getById(knowledgeBase.getRagId());
    }

    @Override
    public void delete(Long ragId) {
        removeById(ragId);
    }
}
