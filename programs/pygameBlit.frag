#version 460

in vec2 v_uv;
out vec4 fragColor;

uniform sampler2D pgTexture;
uniform sampler2D rtTexture;

void main()
{
    vec4 rtColor = vec4( texture( rtTexture, v_uv ).rgba );
    vec4 pgColor = vec4( texture( pgTexture, v_uv ).rgba );
    vec3 color = mix(rtColor.rgb, pgColor.rgb, pgColor.a);
    fragColor = vec4( color, 1.0 );
}
