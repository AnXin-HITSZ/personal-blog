package com.anxin_hitsz.controller.article;

import com.anxin_hitsz.entity.Article;
import com.anxin_hitsz.service.article.IArticleService;
import com.anxin_hitsz.utils.Result;
import com.baomidou.mybatisplus.core.conditions.query.QueryWrapper;
import jakarta.annotation.Resource;
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
     */
    @PostMapping("/add")
    public Result addArticle(@RequestBody Article article) {
        articleService.save(article);
        return Result.ok();
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
