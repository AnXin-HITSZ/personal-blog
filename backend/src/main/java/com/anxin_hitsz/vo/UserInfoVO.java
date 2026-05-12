package com.anxin_hitsz.vo;

import lombok.AllArgsConstructor;
import lombok.Data;
import lombok.NoArgsConstructor;

/**
 * ClassName: UserInfoVO
 * Package: com.anxin_hitsz.vo
 * Description:
 *
 * @Author AnXin
 * @Create 2026/5/12 16:39
 * @Version 1.0
 */
@Data
@NoArgsConstructor
@AllArgsConstructor
public class UserInfoVO {
    /**
     * 用户 ID
     */
    private Long userId;

    /**
     * 用户名
     */
    private String username;

    /**
     * 是否为管理员
     */
    private Integer isAdmin;
}
