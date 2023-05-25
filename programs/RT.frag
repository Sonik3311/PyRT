#version 460

in vec2 v_uv;
out vec4 fragColor;

uniform vec2 u_resolution;
uniform sampler2D geometryTexture;
uniform int geometryCount;
uniform int geometryPixelCount;

uniform int sphereCount;
uniform int cubeCount;


//STRUCTS
struct Ray{
    vec3 origin;
    vec3 direction;
};
struct Material{
    vec3 albedo;
    float roughness;
    float metallness;
    float emissive;
};

vec2 sphIntersect( vec3 ro,  vec3 rd, float ra ){
    float b = dot( ro, rd );
    float c = dot( ro, ro ) - ra*ra;
    float h = b*b - c;
    if( h<0.0 ) return vec2(-1.0); // no intersection
    h = sqrt( h );
    return vec2( -b-h, -b+h ); //-b-h, -b+h
}
vec2 boxIntersection( in vec3 ro, in vec3 rd, vec3 boxSize, out vec3 outNormal ) 
{
    vec3 m = 1.0/rd; // can precompute if traversing a set of aligned boxes
    vec3 n = m*ro;   // can precompute if traversing a set of aligned boxes
    vec3 k = abs(m)*boxSize;
    vec3 t1 = -n - k;
    vec3 t2 = -n + k;
    float tN = max( max( t1.x, t1.y ), t1.z );
    float tF = min( min( t2.x, t2.y ), t2.z );
    if( tN>tF || tF<0.0) {return vec2(-1.0);} // no intersection
    if (tN>0.0){
        outNormal = step(vec3(tN), t1);
    } else {
        outNormal = step(t2,vec3(tF));
    }
    //outNormal = (tN>0.0) ? step(vec3(tN),t1)) : // ro ouside the box
    //                       step(t2,vec3(tF)));  // ro inside the box
    outNormal *= -sign(rd);
    return vec2( tN, tF );
}
//UTILITY
vec4 raycast( in vec3 ro, in vec3 rd, in sampler2D geometryTexture ){

    float minDist = 99999;

    int cubeID = 0;
    vec3 normal;
    vec3 tempNormal;

    struct Material hitMaterial;
    vec2 hitObjID; //x=type,y=geometryIndex

    for (int geometryIndex=0; geometryIndex<geometryCount; geometryIndex++){
        if (geometryIndex < sphereCount){
            float geometryPixelUV = float(geometryIndex+0.5) / geometryPixelCount;
            vec4 sphere = texture(geometryTexture, vec2(geometryPixelUV,0));
            vec2 intersectionResult = sphIntersect( ro-sphere.xyz, rd, sphere.w );
            if (intersectionResult.x > 0 && minDist > intersectionResult.x){
                minDist = intersectionResult.x;
            }
        } else if (geometryIndex < cubeCount+sphereCount){
            float geometryPixel  = float(geometryIndex+0.5+cubeID) / geometryPixelCount;
            float geometryPixel1 = float(geometryIndex+1.5+cubeID) / geometryPixelCount;

            vec3 pos   = texture(geometryTexture, vec2(geometryPixel, 0)).xyz;
            vec3 scale = texture(geometryTexture, vec2(geometryPixel1, 0)).xyz;
            
            vec2 intersectionResult = boxIntersection(ro - pos, rd, scale, tempNormal);
            if (intersectionResult.x > 0.0 && intersectionResult.x < minDist){
                minDist = intersectionResult.x;
                normal = tempNormal;
            }
            cubeID++;
        }
        
        
    }
    if (minDist < 99999){
        return vec4(1);
    }
    return vec4(0);
}







//MAIN
void main()
{   
    vec2 aspect_ratio = u_resolution/u_resolution.y;
    vec2 norm_uv = (v_uv.xy-0.5)*aspect_ratio;
    
    struct Ray ray;
    ray.origin = vec3(-5,0,0);
    ray.direction = normalize( vec3( 1, norm_uv ) );
    vec4 hitColor = raycast( ray.origin, ray.direction, geometryTexture );
    fragColor = vec4(hitColor.rgb,1.0);//texture(geometryTexture, vec2(float(0+0.5)/geometryCount,0));//
}