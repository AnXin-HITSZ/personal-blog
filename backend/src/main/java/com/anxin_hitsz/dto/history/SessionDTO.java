package com.anxin_hitsz.dto.history;

import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;

/**
 * ClassName: SessionDTO
 * Package: com.anxin_hitsz.dto.history
 * Description: 历史会话列表项
 *
 * @Author AnXin
 * @Create 2026/5/2
 * @Version 1.0
 */
@Data
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class SessionDTO {
    private String sessionId;
    private String title;
    private String preview;
    private Long createdAt;
    private Long updatedAt;
    private Integer messageCount;
}
