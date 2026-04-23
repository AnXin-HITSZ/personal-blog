package com.anxin_hitsz.utils;

import com.anxin_hitsz.dto.user.UserDTO;

/**
 * ClassName: UserHolder
 * Package: com.anxin_hitsz.utils
 * Description:
 *
 * @Author AnXin
 * @Create 2026/4/22 21:42
 * @Version 1.0
 */
public class UserHolder {

    private static final ThreadLocal<UserDTO> tl = new ThreadLocal<>();

    public static void saveUser(UserDTO user) {
        tl.set(user);
    }

    public static UserDTO getUser() {
        return tl.get();
    }

    public static void removeUser() {
        tl.remove();
    }
}
