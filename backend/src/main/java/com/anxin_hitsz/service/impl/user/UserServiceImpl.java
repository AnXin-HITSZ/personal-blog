package com.anxin_hitsz.service.impl.user;

import com.anxin_hitsz.entity.User;
import com.anxin_hitsz.mapper.UserMapper;
import com.anxin_hitsz.service.user.IUserService;
import com.baomidou.mybatisplus.extension.service.impl.ServiceImpl;
import org.springframework.stereotype.Service;

/**
 * ClassName: UserServiceImpl
 * Package: com.anxin_hitsz.service.impl
 * Description:
 *
 * @Author AnXin
 * @Create 2026/4/17 15:31
 * @Version 1.0
 */
@Service
public class UserServiceImpl extends ServiceImpl<UserMapper, User> implements IUserService {
}
