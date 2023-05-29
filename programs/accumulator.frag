#version 460

in vec2 v_uv;
out vec4 fragColor;

uniform sampler2D accumFrame;
uniform sampler2D currentFrame;
uniform int frame;

uniform bool accumulate;

void main(){

    //fragColor = texture(currentFrame, v_uv);
    float weight = 1.0 / (frame + 1);
    //vec3 color = texture(lastFrame, v_uv).rgb * (1 - weight) + texture(Tex, v_uv).rgb * weight;
    if (frame==0 || accumulate == false){
        fragColor = texture(currentFrame,v_uv);
    }else{
        
        fragColor = mix(texture(accumFrame, v_uv), texture(currentFrame,v_uv),weight);
    }
    
}