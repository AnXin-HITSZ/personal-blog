package com.anxin_hitsz.controller.rag;

import com.anxin_hitsz.dto.user.UserDTO;
import com.anxin_hitsz.entity.RAGKnowledgeBase;
import com.anxin_hitsz.service.impl.user.account.UserDetailsImpl;
import com.anxin_hitsz.service.rag.IRAGService;
import com.anxin_hitsz.utils.Result;
import com.anxin_hitsz.utils.UserHolder;
import jakarta.annotation.Resource;
import org.springframework.security.core.Authentication;
import org.springframework.web.bind.annotation.*;

import java.util.List;
import java.util.Objects;

/**
 * ClassName: RAGController
 * Package: com.anxin_hitsz.controller.rag
 * Description: 知识库管理控制器
 *
 * @Author AnXin
 * @Create 2026/5/1
 * @Version 1.0
 */
@RestController
@RequestMapping("/api/rag")
public class RAGController {

    @Resource
    private IRAGService ragService;

    /**
     * 获取所有知识库
     */
    @GetMapping("/list")
    public Result list() {
        List<RAGKnowledgeBase> list = ragService.getList();
        return Result.ok(list);
    }

    /**
     * 新增知识库（仅管理员）
     */
    @PostMapping("/add")
    public Result add(
            @RequestBody RAGKnowledgeBase knowledgeBase,
            Authentication authentication
    ) {
        UserDetailsImpl loginUser = (UserDetailsImpl) authentication.getPrincipal();
        if (loginUser == null || !Objects.equals(loginUser.getUser().getUserId(), 1L)) {
            return Result.fail("仅管理员可操作");
        }
        knowledgeBase.setUserId(loginUser.getUser().getUserId());
        RAGKnowledgeBase created = ragService.add(knowledgeBase);
        return Result.ok(created);
    }

    /**
     * 更新知识库（仅管理员）
     */
    @PostMapping("/update")
    public Result update(
            @RequestBody RAGKnowledgeBase knowledgeBase,
            Authentication authentication
    ) {
        UserDetailsImpl loginUser = (UserDetailsImpl) authentication.getPrincipal();
        if (loginUser == null || !Objects.equals(loginUser.getUser().getUserId(), 1L)) {
            return Result.fail("仅管理员可操作");
        }
        RAGKnowledgeBase updated = ragService.update(knowledgeBase);
        return Result.ok(updated);
    }

    /**
     * 删除知识库（仅管理员）
     */
    @PostMapping("/delete/{ragId}")
    public Result delete(
            @PathVariable Long ragId,
            Authentication authentication
    ) {
        UserDetailsImpl loginUser = (UserDetailsImpl) authentication.getPrincipal();
        if (loginUser == null || !Objects.equals(loginUser.getUser().getUserId(), 1L)) {
            return Result.fail("仅管理员可操作");
        }
        ragService.delete(ragId);
        return Result.ok();
    }
}
