package com.anxin_hitsz.entity;

import com.baomidou.mybatisplus.annotation.IdType;
import com.baomidou.mybatisplus.annotation.TableId;
import com.baomidou.mybatisplus.annotation.TableName;
import lombok.AllArgsConstructor;
import lombok.Data;
import lombok.NoArgsConstructor;

import java.time.LocalDateTime;

/**
 * ClassName: Article
 * Package: com.anxin_hitsz.entity
 * Description:
 *
 * @Author AnXin
 * @Create 2026/4/17 15:16
 * @Version 1.0
 */
@Data
@NoArgsConstructor
@AllArgsConstructor
@TableName("tb_article")
public class Article {
    /**
     * 文章 ID
     */
    @TableId(type = IdType.AUTO)
    private Long articleId;

    /**
     * 作者 ID
     */
    private Long userId;

    /**
     * 文章名
     */
    private String title;

    /**
     * 文章内容
     */
    private String content;

    /**
     * 创建日期
     */
    private LocalDateTime createTime;

    /**
     * 更新日期
     */
    private LocalDateTime updateTime;

}
