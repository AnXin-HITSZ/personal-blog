package com.anxin_hitsz.service.user.account;

import com.anxin_hitsz.dto.user.RegisterDTO;
import com.anxin_hitsz.utils.Result;

/**
 * ClassName: IRegisterService
 * Package: com.anxin_hitsz.service.user.account
 * Description:
 *
 * @Author AnXin
 * @Create 2026/4/19 13:59
 * @Version 1.0
 */
public interface IRegisterService {
    Result register(RegisterDTO user);
}
