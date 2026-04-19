package com.anxin_hitsz.service.impl.user.account;

import com.anxin_hitsz.entity.User;
import com.anxin_hitsz.service.user.account.IInfoService;
import com.anxin_hitsz.utils.Result;
import com.anxin_hitsz.vo.UserInfoVO;
import org.springframework.security.authentication.UsernamePasswordAuthenticationToken;
import org.springframework.security.core.context.SecurityContextHolder;
import org.springframework.stereotype.Service;

/**
 * ClassName: InfoServiceImpl
 * Package: com.anxin_hitsz.service.impl.user.account
 * Description:
 *
 * @Author AnXin
 * @Create 2026/4/19 16:04
 * @Version 1.0
 */
@Service
public class InfoServiceImpl implements IInfoService {
    @Override
    public Result getInfo() {
        UsernamePasswordAuthenticationToken authenticationToken = (UsernamePasswordAuthenticationToken) SecurityContextHolder.getContext().getAuthentication();
        if (authenticationToken == null) {
            return Result.fail("authenticationToken 为空");
        }
        UserDetailsImpl loginUser = (UserDetailsImpl) authenticationToken.getPrincipal();
        if (loginUser == null) {
            return Result.fail("登录用户为空");
        }
        User user = loginUser.getUser();
        UserInfoVO userInfoVO = new UserInfoVO();
        userInfoVO.setUserId(user.getUserId());
        userInfoVO.setUsername(user.getUsername());
        return Result.ok(userInfoVO);
    }
}
