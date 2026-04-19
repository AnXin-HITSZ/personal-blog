package com.anxin_hitsz.service.user.account;

import com.anxin_hitsz.dto.LoginDTO;
import com.anxin_hitsz.utils.Result;

/**
 * ClassName: ILoginService
 * Package: com.anxin_hitsz.service.user.account
 * Description:
 *
 * @Author AnXin
 * @Create 2026/4/19 14:45
 * @Version 1.0
 */
public interface ILoginService {
    Result getToken(LoginDTO user);
}
