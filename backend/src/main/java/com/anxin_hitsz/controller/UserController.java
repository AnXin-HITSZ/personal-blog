package com.anxin_hitsz.controller;

import com.anxin_hitsz.entity.User;
import com.anxin_hitsz.service.IUserService;
import com.anxin_hitsz.utils.Result;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.web.bind.annotation.*;

/**
 * ClassName: UserController
 * Package: com.anxin_hitsz.controller
 * Description:
 *
 * @Author AnXin
 * @Create 2026/4/17 15:03
 * @Version 1.0
 */
@RestController
@RequestMapping("/api/user")
public class UserController {
    @Autowired
    private IUserService userService;

    /**
     * 新增用户
     */
    @PostMapping("/add")
    public Result addUser(@RequestBody User user) {
        userService.save(user);
        return Result.ok();
    }

    /**
     * 删除用户
     */
    @PostMapping("/delete/{userId}")
    public Result deleteUser(@PathVariable Long userId) {
        userService.removeById(userId);
        return Result.ok();
    }

}
