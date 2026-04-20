package com.anxin_hitsz.dto.user;

import lombok.AllArgsConstructor;
import lombok.Data;
import lombok.NoArgsConstructor;

/**
 * ClassName: LoginDTO
 * Package: com.anxin_hitsz.dto
 * Description:
 *
 * @Author AnXin
 * @Create 2026/4/19 14:44
 * @Version 1.0
 */
@Data
@NoArgsConstructor
@AllArgsConstructor
public class LoginDTO {
    /**
     * 用户名
     */
    private String username;

    /**
     * 用户密码
     */
    private String password;

}
