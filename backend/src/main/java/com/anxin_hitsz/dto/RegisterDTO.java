package com.anxin_hitsz.dto;

import lombok.AllArgsConstructor;
import lombok.Data;
import lombok.NoArgsConstructor;

/**
 * ClassName: RegisterDTO
 * Package: com.anxin_hitsz.dto
 * Description:
 *
 * @Author AnXin
 * @Create 2026/4/19 13:56
 * @Version 1.0
 */
@Data
@NoArgsConstructor
@AllArgsConstructor
public class RegisterDTO {
    /**
     * 用户名
     */
    private String username;

    /**
     * 用户密码
     */
    private String password;

    /**
     * 确认密码
     */
    private String confirmedPassword;

}
