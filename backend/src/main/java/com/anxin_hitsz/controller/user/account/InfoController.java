package com.anxin_hitsz.controller.user.account;

import com.anxin_hitsz.service.user.account.IInfoService;
import com.anxin_hitsz.utils.Result;
import jakarta.annotation.Resource;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

/**
 * ClassName: InfoController
 * Package: com.anxin_hitsz.controller.user.account
 * Description:
 *
 * @Author AnXin
 * @Create 2026/4/19 16:02
 * @Version 1.0
 */
@RestController
@RequestMapping("/user/account")
public class InfoController {

    @Resource
    private IInfoService infoService;

    /**
     * 向前端请求头提供 token
     */
    @GetMapping("/info")
    public Result getInfo() {
        return infoService.getInfo();
    }
}
