package com.anxin_hitsz.service.impl.article;

import com.anxin_hitsz.entity.Article;
import com.anxin_hitsz.mapper.article.ArticleMapper;
import com.anxin_hitsz.service.article.IArticleService;
import com.baomidou.mybatisplus.extension.service.impl.ServiceImpl;
import org.springframework.stereotype.Service;

/**
 * ClassName: ArticleServiceImpl
 * Package: com.anxin_hitsz.service.impl.article
 * Description:
 *
 * @Author AnXin
 * @Create 2026/4/19 18:59
 * @Version 1.0
 */
@Service
public class ArticleServiceImpl extends ServiceImpl<ArticleMapper, Article> implements IArticleService {
}
