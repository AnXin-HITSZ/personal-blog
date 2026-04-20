package com.anxin_hitsz.service.impl.user.account;

import com.anxin_hitsz.dto.user.LoginDTO;
import com.anxin_hitsz.entity.User;
import com.anxin_hitsz.service.user.account.ILoginService;
import com.anxin_hitsz.utils.JwtUtils;
import com.anxin_hitsz.utils.Result;
import jakarta.annotation.Resource;
import org.springframework.security.authentication.AuthenticationManager;
import org.springframework.security.authentication.UsernamePasswordAuthenticationToken;
import org.springframework.security.core.Authentication;
import org.springframework.stereotype.Service;

/**
 * ClassName: LoginServiceImpl
 * Package: com.anxin_hitsz.service.impl.user.account
 * Description:
 *
 * @Author AnXin
 * @Create 2026/4/19 14:46
 * @Version 1.0
 */
@Service
public class LoginServiceImpl implements ILoginService {

    @Resource
    private JwtUtils jwtUtils;

    @Resource
    private AuthenticationManager authenticationManager;

    @Override
    public Result getToken(LoginDTO userDTO) {
        UsernamePasswordAuthenticationToken authenticationToken = new UsernamePasswordAuthenticationToken(userDTO.getUsername(), userDTO.getPassword());
        Authentication authentication = authenticationManager.authenticate(authenticationToken);
        UserDetailsImpl loginUser = (UserDetailsImpl) authentication.getPrincipal();
        User user = loginUser.getUser();
        String jwt = jwtUtils.generateToken(user.getUserId(), user.getUsername());

        return Result.ok(jwt);
    }
}
