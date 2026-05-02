package com.anxin_hitsz.dto.rag;

import lombok.Data;

/**
 * ClassName: RAGKnowledgeBaseDTO
 * Package: com.anxin_hitsz.dto.rag
 * Description: 知识库数据传输对象
 *
 * @Author AnXin
 * @Create 2026/5/1
 * @Version 1.0
 */
@Data
public class RAGKnowledgeBaseDTO {

    private Long ragId;

    private String name;

    private String description;

    private String namespace;

    private String collectionName;

    private String filePath;

    private Integer fileCount;

    private Integer status;

    private String createdAt;

    private String updatedAt;
}
