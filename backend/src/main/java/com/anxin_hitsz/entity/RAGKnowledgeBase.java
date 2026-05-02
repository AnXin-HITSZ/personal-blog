package com.anxin_hitsz.entity;

import com.baomidou.mybatisplus.annotation.IdType;
import com.baomidou.mybatisplus.annotation.TableId;
import com.baomidou.mybatisplus.annotation.TableName;
import lombok.AllArgsConstructor;
import lombok.Data;
import lombok.NoArgsConstructor;

import java.time.LocalDateTime;

/**
 * ClassName: RAGKnowledgeBase
 * Package: com.anxin_hitsz.entity
 * Description: RAG 知识库实体
 *
 * @Author AnXin
 * @Create 2026/5/1
 * @Version 1.0
 */
@Data
@NoArgsConstructor
@AllArgsConstructor
@TableName("tb_rag")
public class RAGKnowledgeBase {

    /**
     * 知识库 ID
     */
    @TableId(type = IdType.AUTO)
    private Long ragId;

    /**
     * 创建者 ID
     */
    private Long userId;

    /**
     * 知识库名称
     */
    private String name;

    /**
     * 知识库描述
     */
    private String description;

    /**
     * 命名空间（唯一标识）
     */
    private String namespace;

    /**
     * Qdrant 集合名
     */
    private String collectionName;

    /**
     * 知识库文件路径
     */
    private String filePath;

    /**
     * 文件数量
     */
    private Integer fileCount;

    /**
     * 状态：0-未索引，1-已索引，2-索引中
     */
    private Integer status;

    /**
     * 创建时间
     */
    private LocalDateTime createdAt;

    /**
     * 更新时间
     */
    private LocalDateTime updatedAt;
}
