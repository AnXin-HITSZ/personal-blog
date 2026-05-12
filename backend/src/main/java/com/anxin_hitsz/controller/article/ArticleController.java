package com.anxin_hitsz.controller.article;

import com.anxin_hitsz.entity.Article;
import com.anxin_hitsz.service.article.IArticleService;
import com.anxin_hitsz.service.impl.user.account.UserDetailsImpl;
import com.anxin_hitsz.utils.Result;
import jakarta.annotation.Resource;
import org.springframework.security.core.Authentication;
import org.springframework.web.bind.annotation.*;

import java.util.List;

/**
 * ClassName: ArticleController
 * Package: com.anxin_hitsz.controller.article
 * Description:
 *
 * @Author AnXin
 * @Create 2026/5/12 16:35
 * @Version 1.0
 */
@RestController
@RequestMapping("/api/article")
public class ArticleController {

    @Resource
    private IArticleService articleService;

    /**
     * 新增文章
     * 前端用户调用时从 Authentication 提取 userId；
     * Agent 调用时若 Authentication 为空则使用请求体中传入的 userId
     */
    @PostMapping("/add")
    public Result addArticle(@RequestBody Article article, Authentication authentication) {
        // 优先从 JWT 认证中提取 userId（覆盖请求体中的值，防止越权）
        if (authentication != null && authentication.getPrincipal() instanceof UserDetailsImpl) {
            UserDetailsImpl loginUser = (UserDetailsImpl) authentication.getPrincipal();
            article.setUserId(loginUser.getUser().getUserId());
        }
        // 如果认证信息和请求体中都没有 userId，拒绝保存
        if (article.getUserId() == null) {
            return Result.fail("无法识别用户身份，请重新登录");
        }
        if (article.getTitle() == null || article.getTitle().isBlank()) {
            return Result.fail("文章标题不能为空");
        }
        if (article.getContent() == null || article.getContent().isBlank()) {
            return Result.fail("文章内容不能为空");
        }
        articleService.save(article);
        return Result.ok(article);
    }

    /**
     * 删除文章（仅文章作者可操作）
     */
    @DeleteMapping("/delete/{articleId}")
    public Result deleteArticle(@PathVariable Long articleId, Authentication authentication) {
        // 验证用户身份
        if (authentication == null || !(authentication.getPrincipal() instanceof UserDetailsImpl loginUser)) {
            return Result.fail("请先登录");
        }
        // 验证文章所有权
        Article existing = articleService.getById(articleId);
        if (existing == null) {
            return Result.fail("文章不存在");
        }
        if (!existing.getUserId().equals(loginUser.getUser().getUserId())) {
            return Result.fail("无权删除他人的文章");
        }
        articleService.removeById(articleId);
        return Result.ok();
    }

    /**
     * 修改文章（仅文章作者可操作）
     */
    @PutMapping("/edit")
    public Result editArticle(@RequestBody Article article, Authentication authentication) {
        // 验证用户身份
        if (authentication == null || !(authentication.getPrincipal() instanceof UserDetailsImpl loginUser)) {
            return Result.fail("请先登录");
        }
        // 验证文章所有权
        Article existing = articleService.getById(article.getArticleId());
        if (existing == null) {
            return Result.fail("文章不存在");
        }
        if (!existing.getUserId().equals(loginUser.getUser().getUserId())) {
            return Result.fail("无权修改他人的文章");
        }
        // 不允许通过编辑接口修改作者
        article.setUserId(null);
        articleService.updateById(article);
        return Result.ok();
    }

    /**
     * 查询全部文章
     */
    @GetMapping("/all")
    public Result getAllArticle() {
        List<Article> articleList = articleService.list();
        return Result.ok(articleList);
    }
}
