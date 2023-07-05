#version 460

in vec2 v_uv;
out vec4 fragColor;

uniform sampler2D rtTexture;
uniform float u_exposure;

//----------------------------------------------------------------------------------------------------------
// tonemap (credits to Casual shadertoy Path tracing)
//----------------------------------------------------------------------------------------------------------
vec3 LessThan(vec3 f, float value)
{
    return vec3(
        (f.x < value) ? 1.0f : 0.0f,
        (f.y < value) ? 1.0f : 0.0f,
        (f.z < value) ? 1.0f : 0.0f);
}
 
vec3 LinearToSRGB(vec3 rgb)
{
    rgb = clamp(rgb, 0.0f, 1.0f);
     
    return mix(
        pow(rgb, vec3(1.0f / 2.4f)) * 1.055f - 0.055f,
        rgb * 12.92f,
        LessThan(rgb, 0.0031308f)
    );
}
 
vec3 SRGBToLinear(vec3 rgb)
{
    rgb = clamp(rgb, 0.0f, 1.0f);
     
    return mix(
        pow(((rgb + 0.055f) / 1.055f), vec3(2.4f)),
        rgb / 12.92f,
        LessThan(rgb, 0.04045f)
    );
}

// ACES tone mapping curve fit to go from HDR to LDR
//https://knarkowicz.wordpress.com/2016/01/06/aces-filmic-tone-mapping-curve/
vec3 ACESFilm(vec3 x)
{
    float a = 2.51;
    float b = 0.03;
    float c = 2.43;
    float d = 0.59;
    float e = 0.14;
    return clamp((x*(a*x + b)) / (x*(c*x + d) + e), 0.0f, 1.0f);
}

//----------------------------------------------------------------------------------------------------------
// main
//----------------------------------------------------------------------------------------------------------

float c_exposure = 2;

void main()
{
    vec3 rtColor = texture( rtTexture, v_uv ).rgb;
    rtColor *= u_exposure;
    rtColor = ACESFilm(rtColor);
    rtColor = LinearToSRGB(rtColor);//mix(rtColor.rgb, pgColor.rgb, pgColor.a);
    fragColor = vec4( rtColor, 1.0 );
}
