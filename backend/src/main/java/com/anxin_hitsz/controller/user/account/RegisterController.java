package com.anxin_hitsz.controller.user.account;

import com.anxin_hitsz.dto.user.RegisterDTO;
import com.anxin_hitsz.service.user.account.IRegisterService;
import com.anxin_hitsz.utils.Result;
import jakarta.annotation.Resource;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

/**
 * ClassName: RegisterController
 * Package: com.anxin_hitsz.controller.user.account
 * Description:
 *
 * @Author AnXin
 * @Create 2026/4/19 13:23
 * @Version 1.0
 */
@RestController
@RequestMapping("/user/account")
public class RegisterController {

    @Resource
    private IRegisterService registerService;

    /**
     * 新用户注册
     */
    @PostMapping("/register")
    public Result register(@RequestBody RegisterDTO user) {
        return registerService.register(user);
    }
}
