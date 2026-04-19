package com.anxin_hitsz.controller.user.account;

import com.anxin_hitsz.dto.LoginDTO;
import com.anxin_hitsz.service.user.account.ILoginService;
import com.anxin_hitsz.utils.Result;
import jakarta.annotation.Resource;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

/**
 * ClassName: LoginController
 * Package: com.anxin_hitsz.controller.user.account
 * Description:
 *
 * @Author AnXin
 * @Create 2026/4/19 14:42
 * @Version 1.0
 */
@RestController
@RequestMapping("/user/account")
public class LoginController {

    @Resource
    private ILoginService loginService;

    @PostMapping("/login")
    public Result login(@RequestBody LoginDTO user) {
        return loginService.getToken(user);
    }
}
