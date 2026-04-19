package com.anxin_hitsz.utils;

import cn.hutool.jwt.JWT;
import cn.hutool.jwt.JWTUtil;

import java.util.HashMap;
import java.util.Map;

/**
 * ClassName: JwtUtils
 * Package: com.anxin_hitsz.utils
 * Description:
 *
 * @Author AnXin
 * @Create 2026/4/19 15:30
 * @Version 1.0
 */
public class JwtUtils {

    private static final String SECRET_KEY = "";

    public static String generateToken(Long userId, String username) {
        Map<String, Object> payload = new HashMap<>();
        payload.put("userId", userId);
        payload.put("username", username);
        payload.put("iat", System.currentTimeMillis());
        payload.put("exp", System.currentTimeMillis() + 1000 * 60 * 60 * 24);

        return JWTUtil.createToken(payload, SECRET_KEY.getBytes());
    }

    public static boolean validateToken(String token) {
        try {
            return JWTUtil.verify(token, SECRET_KEY.getBytes());
        } catch (Exception e) {
            return false;
        }
    }

    public static Long getUserId(String token) {
        JWT jwt = JWTUtil.parseToken(token);
        return Long.valueOf(jwt.getPayload("userId").toString());
    }

    public static String getUsername(String token) {
        JWT jwt = JWTUtil.parseToken(token);
        return jwt.getPayload("username").toString();
    }
}
