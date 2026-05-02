package com.anxin_hitsz.controller.article;

import com.anxin_hitsz.entity.Article;
import com.anxin_hitsz.service.article.IArticleService;
import com.anxin_hitsz.service.impl.user.account.UserDetailsImpl;
import com.anxin_hitsz.utils.Result;
import com.baomidou.mybatisplus.core.conditions.query.QueryWrapper;
import jakarta.annotation.Resource;
import org.springframework.security.core.Authentication;
import org.springframework.web.bind.annotation.*;

import java.util.List;

/**
 * ClassName: ArticleController
 * Package: com.anxin_hitsz.controller
 * Description:
 *
 * @Author AnXin
 * @Create 2026/4/17 15:05
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
        if (authentication != null && authentication.getPrincipal() instanceof UserDetailsImpl) {
            UserDetailsImpl loginUser = (UserDetailsImpl) authentication.getPrincipal();
            article.setUserId(loginUser.getUser().getUserId());
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
     * 删除文章
     */
    @DeleteMapping("/delete/{articleId}")
    public Result deleteArticle(@PathVariable Long articleId) {
        articleService.removeById(articleId);
        return Result.ok();
    }

    /**
     * 修改文章
     */
    @PutMapping("/edit")
    public Result editArticle(@RequestBody Article article) {
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
