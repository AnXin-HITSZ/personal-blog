package com.anxin_hitsz.service.impl.user.account;

import cn.hutool.core.util.StrUtil;
import com.anxin_hitsz.dto.RegisterDTO;
import com.anxin_hitsz.entity.User;
import com.anxin_hitsz.mapper.user.UserMapper;
import com.anxin_hitsz.service.user.account.IRegisterService;
import com.anxin_hitsz.utils.Result;
import com.baomidou.mybatisplus.core.conditions.query.QueryWrapper;
import jakarta.annotation.Resource;
import org.springframework.security.crypto.password.PasswordEncoder;
import org.springframework.stereotype.Service;

import java.util.List;

/**
 * ClassName: RegisterServiceImpl
 * Package: com.anxin_hitsz.service.impl.user.account
 * Description:
 *
 * @Author AnXin
 * @Create 2026/4/19 14:00
 * @Version 1.0
 */
@Service
public class RegisterServiceImpl implements IRegisterService {

    @Resource
    private UserMapper userMapper;

    @Resource
    private PasswordEncoder passwordEncoder;

    @Override
    public Result register(RegisterDTO user) {
        String username = user.getUsername().trim();
        if (StrUtil.isBlank(user.getUsername())) {
            return Result.fail("用户名不能为空");
        }
        if (user.getUsername().length() > 100) {
            return Result.fail("用户名长度不能大于 100");
        }

        if (StrUtil.isBlank(user.getPassword()) || StrUtil.isBlank(user.getConfirmedPassword())) {
            return Result.fail("密码不能为空");
        }
        if (user.getPassword().length() > 100) {
            return Result.fail("密码长度不能大于 100");
        }
        if (!user.getPassword().equals(user.getConfirmedPassword())) {
            return Result.fail("两次输入的密码不一致");
        }

        QueryWrapper<User> queryWrapper = new QueryWrapper<>();
        queryWrapper.eq("username", user.getUsername());
        List<User> users = userMapper.selectList(queryWrapper);
        if (!users.isEmpty()) {
            return Result.fail("用户名已存在");
        }

        String encodePassword = passwordEncoder.encode(user.getPassword());
        User newUser = new User(null, user.getUsername(), encodePassword, 0, null, null);
        userMapper.insert(newUser);

        return Result.ok();

    }
}
