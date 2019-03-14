"""
This is a one time setup for cognito user pools.
The public keys of the user pool has to be extracted from the url:
https://cognito-idp.{region}.amazonaws.com/{cognito user pool id}/.well-known/jwks.json
"""
cognito_user_pool_jwks = \
    {
        "envs":
        [
            {
                "name": "dev",
                "keys":
                    [
                        {
                            "alg": "RS256",
                            "e": "AQAB",
                            "kid": "X4VjDuyNNyvzVaent1aMu4t52jOnERv2lFNjX3z5vS4=",
                            "kty": "RSA",
                            "n": "hPHuw101gg3r6pdazc2GEp2Gm0I2IzKhQyQqzBSbHQkS2VQ5XPOa9mjNA4T2t7cPuLpnR_m1VbVTtIIAT1Td1V6DU_5788ugPIPlbWheUJ8clOxMOqaZqLzqk0Snnl4Erq2o7wwANSo76HxBlzqPERKv35xHp_8DSH4G9NrguUL87KMPbK1lT5bX23_VcjBLQ-cLfYJ9HVyJcy5icFsjEsZe-vUikpowd1p58QFO7h05mPYEye-8egh26WaTKWDebX0r763dh2sn4bQGhgyy0fjErVvWuDUFvyzBD9qMyOvyAEJ9Mtcxkv2zz_N6Q27QuNnV5qpeoAWY9dbmq26I-Q",
                            "use": "sig"
                        },
                        {
                            "alg": "RS256",
                            "e": "AQAB",
                            "kid": "UWfORtTliW71/yapWmaOvqRVbVQM/uYq7m+grnLWTNQ=",
                            "kty": "RSA",
                            "n": "mZWV-NfT9aj_eQfrcAfGrvdZ0Oo8xXWeP5l6cJQDJxRLM7rpyMcnIp6eux9xvilq0MPqIDgosuWagAVWf29m0LdiTVVB09zFYFGMJGLEw2nZ9ANVioS7sPthrTN7CvcyFZCwKhyjLak0E9_ldtUwSMYWbXmHiVOnwHo3hj8SWjTCINqGoIp35vc0At7RyMrJIgro7r5pzzOMrpWgA-s96uj3VyvHB4qYyhqEntheMeR153JU1En99eoFMy0Av4Cl0GUFLUku30K1t7_ATH7dvoQAkgVjcLT_0pQ8S-FEuJxCFUM6XET7SE5DzTIsqaiHXUYFttsI1YBU_rd9AG7bmQ",
                            "use": "sig"
                        }
                    ]
            },
            {
                "name": "prod",
                "keys":
                    [
                        {
                            "alg": "RS256",
                            "e": "AQAB",
                            "kid": "Lso7pwmrqxSkeH0zrw3OZX+aL/ncHQfrSxXm0jt5T0A=",
                            "kty": "RSA",
                            "n": "mCfb6gOHhFx-aqN_ppJRNvM-emvcJb68IuvhHjv1QwAo2veV6m0MLppURM7Ptit-iz5QlQlTCvJy2DNashgmFtxQG8xo9B70mg5tlMr-IIhEVoBAAr2CE6axQ_ntSKq6Vfm5gP_oB-nYS4xTJl_kFOo1cQMCpr9i6BHqvkuyqUVG2WkSbj5Pm9ngFgK_Q4gMnWpOC9avdvTUK1nuy8X0cqOCIgiIwecU47XUylKytEprTv90vnwkbKZQMxbiQqKoU9J-PChQB8yU4fR1WcdPFDxTc8il8q-WhRIxdFq5JVFqZLzalMOm9qJoduMKIs36rJOPmVRtIJ3zTMSUI9xDDw",
                            "use": "sig"
                        },
                        {
                            "alg": "RS256",
                            "e": "AQAB",
                            "kid": "N37y5vOkPQfwt6cthBIvCIvEfz+bcbIfn3vr/W3E43o=",
                            "kty": "RSA",
                            "n": "gQkOhzCAtsFIeJj3-mGnEUduHnUGrpF-NQh5uryRbVvjJZ6FBz4-LVNGfMz-xJeLo9MkKz7MNg-_laFie5qQZbpmIAWjlgDpwnHtvUXhxXLOZYFBeKdvLWvD8Kvo2Zz3jf4PfoRh2YbrgQhHXtg-x_XlvueB6JMx0pN1n5NunopjHWMyI2fAEVZaxKQQdt2TFXCh9p5Ys8xkzXswLhBXOEyOR37WozzsgjJN2ER-6yOsL7qjhwqb_zDEQ4qztSZlv3KdE_cLgkBBkB_fCaIqg98Sv7CD-vx7BzoxhboJ4-Dt3Z6lmZbcrd4XXQEagianlnGsYq9RdrE36EJW4l6hRQ",
                            "use": "sig"
                        }
                ]
            }
        ]
    }
