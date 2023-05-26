#version 460

in vec2 v_uv;
out vec4 fragColor;

uniform vec2 u_resolution;
uniform sampler2D geometryTexture;
uniform sampler2D materialTexture;
uniform int geometryCount;
uniform int geometryPixelCount;

uniform int sphereCount;
uniform int cubeCount;
uniform int cylinderCount;


//STRUCTS
struct rayStruct{
    vec3 origin;
    vec3 direction;
};
struct materialStruct{
    vec3 albedo;
    vec3 specularColor;
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

// cylinder defined by extremes a and b, and radious ra
vec4 cylIntersect( in vec3 ro, in vec3 rd, in vec3 a, in vec3 b, float ra )
{
    vec3  ba = b  - a;
    vec3  oc = ro - a;
    float baba = dot(ba,ba);
    float bard = dot(ba,rd);
    float baoc = dot(ba,oc);
    float k2 = baba            - bard*bard;
    float k1 = baba*dot(oc,rd) - baoc*bard;
    float k0 = baba*dot(oc,oc) - baoc*baoc - ra*ra*baba;
    float h = k1*k1 - k2*k0;
    if( h<0.0 ) return vec4(-1.0);//no intersection
    h = sqrt(h);
    float t = (-k1-h)/k2;
    // body
    float y = baoc + t*bard;
    if( y>0.0 && y<baba ) return vec4( t, (oc+t*rd - ba*y/baba)/ra );
    // caps
    t = ( ((y<0.0) ? 0.0 : baba) - baoc)/bard;
    if( abs(k1+k2*t)<h )
    {
        return vec4( t, ba*sign(y)/sqrt(baba) );
    }
    return vec4(-1.0);//no intersection
}

// normal at point p of cylinder (a,b,ra), see above
vec3 cylNormal( in vec3 p, in vec3 a, in vec3 b, float ra )
{
    vec3  pa = p - a;
    vec3  ba = b - a;
    float baba = dot(ba,ba);
    float paba = dot(pa,ba);
    float h = dot(pa,ba)/baba;
    return (pa - ba*h)/ra;
}
//UTILITY
vec4 raycast( in vec3 ro, in vec3 rd, out materialStruct hitMaterial, out vec3 hitpoint, out vec3 hitNormal ){

    float minDist = 99999;
    vec3 tempNormal;

    int materialPixelCount = geometryCount * 3;
    vec3 hitObjID; //x=type,y=geometryIndex,z=pixelIndex
    
    int pixelIndex = 0;
    for (int geometryIndex=0; geometryIndex<geometryCount; geometryIndex++){
        if (geometryIndex < sphereCount){
            vec2 geometryUV = vec2(float(pixelIndex+0.5) / geometryPixelCount, 0);
            vec4 sphere = texture(geometryTexture, geometryUV);
            vec2 intersection = sphIntersect(ro-sphere.xyz, rd, sphere.w);
            if (intersection.x > 0 && minDist > intersection.x){
                hitpoint = ro + rd*intersection.x;
                hitNormal = normalize(hitpoint-sphere.xyz);
                minDist = intersection.x;
                hitObjID.x = 1;
                hitObjID.y = geometryIndex;
                hitObjID.z = pixelIndex;
            }
            pixelIndex += 1;
        } else if (sphereCount <= geometryIndex && geometryIndex < (sphereCount + cubeCount)){
            vec2 geometryUV1 = vec2(float(pixelIndex+0.5) / geometryPixelCount, 0);
            vec2 geometryUV2 = vec2(float(pixelIndex+1.5) / geometryPixelCount, 0);

            vec3 pos  = texture(geometryTexture, geometryUV1).xyz;
            vec3 size = texture(geometryTexture, geometryUV2).xyz;

            vec2 intersection = boxIntersection(ro - pos, rd, size, tempNormal);
            if (intersection.x > 0.0 && intersection.x < minDist){
                hitpoint = ro + rd*intersection.x;
                minDist = intersection.x;
                hitNormal = tempNormal;
                hitObjID.x = 2;
                hitObjID.y = geometryIndex;
                hitObjID.z = pixelIndex;
            }
            pixelIndex += 2;
        } else if ((sphereCount + cubeCount) <= geometryIndex && geometryIndex < (sphereCount + cubeCount + cylinderCount)){
            vec2 geometryUV1 = vec2(float(pixelIndex+0.5) / geometryPixelCount, 0);
            vec2 geometryUV2 = vec2(float(pixelIndex+1.5) / geometryPixelCount, 0);
            
            vec3 posA = texture(geometryTexture, geometryUV1).xyz;
            vec3 posB = texture(geometryTexture, geometryUV2).xyz;
            float radius = texture(geometryTexture, geometryUV1).w;

            vec4 intersection = cylIntersect( ro, rd, posA, posB, radius );
            if (intersection.x > 0.0 && intersection.x < minDist){
                hitpoint = ro + rd*intersection.x;
                minDist = intersection.x;
                hitNormal = intersection.yzw;
                hitObjID.x = 3;
                hitObjID.y = geometryIndex;
                hitObjID.z = pixelIndex;
            }
            pixelIndex += 2;
        }     
    }
    if (minDist < 99999){
        vec2 materialUV1 = vec2(float(hitObjID.y*3+0.5) / materialPixelCount);
        vec2 materialUV2 = vec2(float(hitObjID.y*3+1.5) / materialPixelCount);
        vec2 materialUV3 = vec2(float(hitObjID.y*3+2.5) / materialPixelCount);

        vec4 materialPixel1 = texture(materialTexture, materialUV1);
        vec4 materialPixel2 = texture(materialTexture, materialUV2);
        vec4 materialPixel3 = texture(materialTexture, materialUV3);

        hitMaterial.albedo = materialPixel1.rgb;
        hitMaterial.specularColor = materialPixel2.rgb;
        hitMaterial.roughness = materialPixel3.r;
        hitMaterial.metallness = materialPixel3.g;
        hitMaterial.emissive = materialPixel3.b;
        return vec4(1);
    }
    return vec4(0);
}







//MAIN
void main()
{   
    vec2 aspect_ratio = u_resolution/u_resolution.y;
    vec2 norm_uv = (v_uv.xy-0.5)*aspect_ratio;
    
    struct rayStruct ray;
    ray.origin = vec3(5,0,0);
    ray.direction = normalize( vec3( -1, norm_uv ) );
    struct materialStruct hitMaterial;
    vec3 hitnormal;
    vec3 hitpoint;
    vec4 hit = raycast( ray.origin, ray.direction, hitMaterial, hitpoint, hitnormal);//texture(geometryTexture, vec2(b, 0));
    vec3 hitColor = vec3(0);
    if (hit.x > 0){
        hitColor = hitnormal;
    }
    fragColor = vec4(hitColor,1.0);//texture(geometryTexture, vec2(float(0+0.5)/geometryCount,0));//
}