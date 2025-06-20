#version 460

in vec2 v_uv;
out vec4 fragColor;

uniform vec2 u_resolution;
uniform int u_frame;
uniform int u_max_samples;
uniform int u_max_reflections;
uniform int u_skybox_type;

uniform vec2 u_mousePos;
uniform vec3 u_cameraPos;

uniform sampler2D u_geometry_texture;
uniform sampler2D u_material_texture;
uniform sampler2D u_skybox_texture;

uniform int u_geometry_count;
uniform int u_geometry_pixel_count;

uniform int u_sphere_count;
uniform int u_cube_count;
uniform int u_cylinder_count;
uniform int u_quad_count;



const float PI = 3.14159265;

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

//----------------------------------------------------------------------------------------------------------
// randomness (credits to Casual shadertoy Path tracing)
//----------------------------------------------------------------------------------------------------------
uint rngState;
uint wang_hash(inout uint seed)
{
    seed = uint(seed ^ uint(61)) ^ uint(seed >> uint(16));
    seed *= uint(9);
    seed = seed ^ (seed >> 4);
    seed *= uint(0x27d4eb2d);
    seed = seed ^ (seed >> 15);
    return seed;
}
 
float RandomFloat01(inout uint state)
{
    return float(wang_hash(state)) / 4294967296.0;
}
 
vec3 RandomUnitVector(inout uint state)
{
    float z = RandomFloat01(state) * 2.0f - 1.0f;
    float a = RandomFloat01(state) * PI*2;
    float r = sqrt(1.0f - z * z);
    float x = r * cos(a);
    float y = r * sin(a);
    return vec3(x, y, z);
}
vec3 RandomHemisphereVector(inout uint state, in vec3 n){
    vec3 v = RandomUnitVector(state);
    return normalize(dot(v,n) * v);
}


//----------------------------------------------------------------------------------------------------------
// structs
//----------------------------------------------------------------------------------------------------------
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
    float refractive;
};
//----------------------------------------------------------------------------------------------------------
// intersections
//----------------------------------------------------------------------------------------------------------
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


float ScalarTriple(vec3 u, vec3 v, vec3 w)
{
    return dot(cross(u, v), w);
}
vec4 quadIntersect(in vec3 rayPos, in vec3 rayDir, in vec3 a, in vec3 b, in vec3 c, in vec3 d)
{
    // calculate normal and flip vertices order if needed
    vec3 normal = normalize(cross(c-a, c-b));
    if (dot(normal, rayDir) > 0.0f)
    {
        normal *= -1.0f;
        
		vec3 temp = d;
        d = a;
        a = temp;
        
        temp = b;
        b = c;
        c = temp;
    }
    
    vec3 p = rayPos;
    vec3 q = rayPos + rayDir;
    vec3 pq = q - p;
    vec3 pa = a - p;
    vec3 pb = b - p;
    vec3 pc = c - p;
    
    // determine which triangle to test against by testing against diagonal first
    vec3 m = cross(pc, pq);
    float v = dot(pa, m);
    vec3 intersectPos;
    if (v >= 0.0f)
    {
        // test against triangle a,b,c
        float u = -dot(pb, m);
        if (u < 0.0f) return vec4(-1);
        float w = ScalarTriple(pq, pb, pa);
        if (w < 0.0f) return vec4(-1);
        float denom = 1.0f / (u+v+w);
        u*=denom;
        v*=denom;
        w*=denom;
        intersectPos = u*a+v*b+w*c;
    }
    else
    {
        vec3 pd = d - p;
        float u = dot(pd, m);
        if (u < 0.0f) return vec4(-1);
        float w = ScalarTriple(pq, pa, pd);
        if (w < 0.0f) return vec4(-1);
        v = -v;
        float denom = 1.0f / (u+v+w);
        u*=denom;
        v*=denom;
        w*=denom;
        intersectPos = u*a+v*d+w*c;
    }
    
    float dist;
    if (abs(rayDir.x) > 0.1f)
    {
        dist = (intersectPos.x - rayPos.x) / rayDir.x;
    }
    else if (abs(rayDir.y) > 0.1f)
    {
        dist = (intersectPos.y - rayPos.y) / rayDir.y;
    }
    else
    {
        dist = (intersectPos.z - rayPos.z) / rayDir.z;
    }
    
	if (dist > 0)
    {       
        return vec4(dist,normal);
    }    
    
    return vec4(-1);
}

//----------------------------------------------------------------------------------------------------------
// materials
//----------------------------------------------------------------------------------------------------------
float myrefract(inout vec3 dir, vec3 n, float N) // return fres (N supposed to be >1)
{
    float dn=dot(dir,n);
    float fres=1.-abs(dot(dir,n));
    fres*=fres*fres;
    fres=.1+.9*fres;
    if (dn>0.) { N=1./N; }
    vec3 ds=dir-dn*n;
    if(length(ds)*(1.-1./N)>1.) {  // total reflection
        dir=reflect(dir,n); return 1.;
    }
    dir-=ds*(1.-1./N);
    if (dn>0.) {
        fres=1.-abs(dot(dir,n));
        fres*=fres*fres;
        fres=.2+.8*fres;
    }
    dir=normalize(dir);
    return fres;
}

float FresnelSchlick(float nIn, float nOut, vec3 direction, vec3 normal)
{
    float R0 = ((nOut - nIn) * (nOut - nIn)) / ((nOut + nIn) * (nOut + nIn));
    float fresnel = R0 + (1.0 - R0) * pow((1.0 - abs(dot(direction, normal))), 5.0);
    return fresnel;
}

//----------------------------------------------------------------------------------------------------------
// quaternions
//----------------------------------------------------------------------------------------------------------

//vec3 Rotate(vec4 q, vec3 v) {
//    float x = q.x * 2.0;
//    float y = q.y * 2.0;
//    float z = q.z * 2.0;
//    float xx = q.x * x;
//    float yy = q.y * y;
//    float zz = q.z * z;
//    float xy = q.x * y;
//    float xz = q.x * z;
//    float yz = q.y * z;
//    float wx = q.w * x;
//    float wy = q.w * y;
//    float wz = q.w * z;
//
//    vec3 rotated;
//    rotated.x = (1f - (yy + zz)) * v.x + (xy - wz) * v.y + (xz + wy) * v.z;
//    rotated.y = (xy + wz) * v.x + (1f - (xx + zz)) * v.y + (yz - wx) * v.z;
//    rotated.z = (xz - wy) * v.x + (yz + wx) * v.y + (1f - (xx + yy)) * v.z;
//    return rotated;
//}

vec4 Q_rotate(vec4 q1, vec4 q2){
    vec4 q;
    q.x = (q1.w * q2.x) + (q1.x * q2.w) + (q1.y * q2.z) - (q1.z * q2.y);
    q.y = (q1.w * q2.y) - (q1.x * q2.z) + (q1.y * q2.w) + (q1.z * q2.x);
    q.z = (q1.w * q2.z) + (q1.x * q2.y) - (q1.y * q2.x) + (q1.z * q2.w);
    q.w = (q1.w * q2.w) - (q1.x * q2.x) - (q1.y * q2.y) - (q1.z * q2.z);
    return q;
}

vec4 Q_inverse(vec4 q){
    return vec4(-q.xyz, q.w);
}

vec3 q_rotate_v(vec4 q, vec3 v){
    vec4 qv = vec4(v, 0);
    vec4 qi = Q_inverse(q);
    vec4 mult = Q_rotate(Q_rotate(q, qv), qi); // q * qv * qi
    return mult.xyz;
}

vec4 Slerp(vec4 p0, vec4 p1, float t)
{
  float dotp = dot(normalize(p0), normalize(p1));
  if ((dotp > 0.9999) || (dotp<-0.9999))
  {
    if (t<=0.5)
      return p0;
    return p1;
  }
  float theta = acos(dotp);
  vec4 P = ((p0*sin((1-t)*theta) + p1*sin(t*theta)) / sin(theta));
  P.w = 1;
  return P;
}

//----------------------------------------------------------------------------------------------------------
// path tracing
//----------------------------------------------------------------------------------------------------------
bool raycast( in vec3 ro, in vec3 rd, out materialStruct hitMaterial, out vec3 hitpoint, out vec3 hitNormal ){

    float minDist = 99999;
    vec3 tempNormal;

    int materialPixelCount = u_geometry_count * 3;
    vec3 hitObjID; //x=type,y=geometryIndex,z=pixelIndex
    
    int pixelIndex = 0;
    for (int geometryIndex=0; geometryIndex<u_geometry_count; geometryIndex++){
        if (geometryIndex < u_sphere_count){
            vec2 geometryUV = vec2(float(pixelIndex+0.5) / u_geometry_pixel_count, 0);
            vec2 quaternionUV = vec2(float(pixelIndex+1.5) / u_geometry_pixel_count, 0);
            
            vec4 sphere = texture(u_geometry_texture, geometryUV);
            vec4 quaternion = texture(u_geometry_texture, quaternionUV); // bruh it's a perfect sphere, why would we need to rotate it?

            vec2 intersection = sphIntersect(ro-sphere.xyz, rd, sphere.w);
            if (intersection.x > 0 && minDist > intersection.x){
                hitpoint = ro + rd*(intersection.x);
                hitNormal = normalize(hitpoint-sphere.xyz);
                minDist = intersection.x;
                hitObjID.x = 1;
                hitObjID.y = geometryIndex;
                hitObjID.z = pixelIndex;
            }
            pixelIndex += 2;
        } else if (u_sphere_count <= geometryIndex && geometryIndex < (u_sphere_count + u_cube_count)){
            vec2 geometryUV1 = vec2(float(pixelIndex+0.5) / u_geometry_pixel_count, 0);
            vec2 geometryUV2 = vec2(float(pixelIndex+1.5) / u_geometry_pixel_count, 0);
            vec2 quaternionUV = vec2(float(pixelIndex+2.5) / u_geometry_pixel_count, 0);

            vec3 pos  = texture(u_geometry_texture, geometryUV1).xyz;
            vec3 size = texture(u_geometry_texture, geometryUV2).xyz;
            vec4 quaternion = texture(u_geometry_texture, quaternionUV);
            // TODO: Rotations with proper normals
            vec3 qro = q_rotate_v(Q_inverse(quaternion), ro-pos);//Rotate(quaternion, ro-pos);
            vec3 qrd = q_rotate_v(Q_inverse(quaternion), rd);//Rotate(quaternion, rd);

            vec2 intersection = boxIntersection(qro, qrd, size, tempNormal);
            if (intersection.x > 0.0 && intersection.x < minDist){
                vec4 invQ = Q_inverse(quaternion);
                hitpoint = q_rotate_v(quaternion, qro) + pos + q_rotate_v(quaternion,qrd)*(intersection.x);
                minDist = intersection.x;
                hitNormal = q_rotate_v(quaternion, tempNormal);//normalize(Rotate(Slerp(quaternion, vec4(0,0,0,1), 0), tempNormal).xyz);//quat_mult(quat_mult(quaternion, vec4(tempNormal,0)), quat_inverse(quaternion)).xyz; //q * v * q^-1
                hitObjID.x = 2;
                hitObjID.y = geometryIndex;
                hitObjID.z = pixelIndex;
            }
            pixelIndex += 3;
        } else if ((u_sphere_count + u_cube_count) <= geometryIndex && geometryIndex < (u_sphere_count + u_cube_count + u_cylinder_count)){
            vec2 geometryUV1 = vec2(float(pixelIndex+0.5) / u_geometry_pixel_count, 0);
            vec2 geometryUV2 = vec2(float(pixelIndex+1.5) / u_geometry_pixel_count, 0);
            vec2 quaternionUV = vec2(float(pixelIndex+2.5) / u_geometry_pixel_count, 0);
            
            vec3 posA = texture(u_geometry_texture, geometryUV1).xyz;
            vec3 posB = texture(u_geometry_texture, geometryUV2).xyz;
            vec3 median = mix(posA,posB,0.5);
            float radius = texture(u_geometry_texture, geometryUV2).w;
            vec4 quaternion = texture(u_geometry_texture, quaternionUV);

            vec4 intersection = cylIntersect(ro, rd, posA, posB, radius);
            if (intersection.x > 0.0 && intersection.x < minDist){
                hitpoint = ro + rd*(intersection.x);
                minDist = intersection.x;
                hitNormal = intersection.yzw;
                hitObjID.x = 3;
                hitObjID.y = geometryIndex;
                hitObjID.z = pixelIndex;
            }
            pixelIndex += 3;
        } else if ((u_sphere_count + u_cube_count + u_cylinder_count) <= geometryIndex && geometryIndex < (u_sphere_count + u_cube_count + u_cylinder_count + u_quad_count)){
            vec2 geometryUV1 = vec2(float(pixelIndex+0.5) / u_geometry_pixel_count, 0);
            vec2 geometryUV2 = vec2(float(pixelIndex+1.5) / u_geometry_pixel_count, 0);
            vec2 geometryUV3 = vec2(float(pixelIndex+2.5) / u_geometry_pixel_count, 0);
            vec2 quaternionUV = vec2(float(pixelIndex+3.5) / u_geometry_pixel_count, 0);

            vec4 pix1 = texture(u_geometry_texture, geometryUV1);
            vec4 pix2 = texture(u_geometry_texture, geometryUV2);
            vec4 pix3 = texture(u_geometry_texture, geometryUV3);
            vec4 quaternion = mix(texture(u_geometry_texture, quaternionUV),vec4(0,0,0,1), 0);
            pixelIndex += 4;

            vec3 A = pix1.xyz;
            vec3 B = pix2.xyz;
            vec3 C = pix3.xyz;
            vec3 D = vec3(pix1.w, pix2.w, pix3.w);
                        
           // vec4 quat = vec4(0.276,0.321,0.276,0.863);
            //vec4 quat = vec4(0,0,0,1);
            vec4 intersection = quadIntersect(ro, rd, A,B,C,D);
            if (intersection.x > 0.0 && intersection.x < minDist){
                hitpoint = ro + rd*(intersection.x);
                minDist = intersection.x;
                hitNormal = intersection.yzw;
                hitObjID.x = 4;
                hitObjID.y = geometryIndex;
                hitObjID.z = pixelIndex;
            }

        }     
    }
    if (minDist < 99999){
        vec2 materialUV1 = vec2(float(hitObjID.y*3+0.5) / materialPixelCount);
        vec2 materialUV2 = vec2(float(hitObjID.y*3+1.5) / materialPixelCount);
        vec2 materialUV3 = vec2(float(hitObjID.y*3+2.5) / materialPixelCount);

        vec4 materialPixel1 = texture(u_material_texture, materialUV1);
        vec4 materialPixel2 = texture(u_material_texture, materialUV2);
        vec4 materialPixel3 = texture(u_material_texture, materialUV3);

        hitMaterial.albedo = materialPixel1.rgb;
        hitMaterial.specularColor = materialPixel2.rgb;
        hitMaterial.roughness = materialPixel3.r;
        hitMaterial.metallness = materialPixel3.g;
        hitMaterial.emissive = materialPixel3.b;
        hitMaterial.refractive = materialPixel3.a;
        return true;
    }
    return false;
}


vec3 getSkyboxColor( in vec3 rd ){
    vec3 col;
    if (u_skybox_type == 0){
        vec2 uv = vec2(0.5 + atan(rd.x, rd.z)/(2*PI), 0.5 + asin(-rd.y)/PI);
        col = vec3(max(sin(uv.x*100)*100 * cos(uv.y*100)*100,0), 0, max(sin(uv.x*100)*100 * cos(uv.y*100)*100,0)); 
        //col = vec3(0);
    } else if (u_skybox_type == 1) {
        col = texture(u_skybox_texture, vec2(0.5 + atan(rd.x, rd.z)/(2*PI), 0.5 + asin(-rd.y)/PI)).xyz;
    }
    return col;
}

vec3 rayTraceSample( in rayStruct ray, in int smple ){
    vec3 color = vec3(0);
    vec3 rayColor = vec3(1);
    struct rayStruct duplicateRay;
    duplicateRay.origin = ray.origin;
    duplicateRay.direction = ray.direction;
    struct materialStruct hitMaterial;
    vec3 hitpoint;
    vec3 hitnormal;
    for (int relfections=0; relfections<u_max_reflections; relfections++){
        bool raycastResult = raycast( duplicateRay.origin, duplicateRay.direction, hitMaterial, hitpoint, hitnormal );
        if (raycastResult == false){ //no hit
            color += SRGBToLinear(getSkyboxColor(duplicateRay.direction))    * rayColor;
            break;
        }

        color += (hitMaterial.albedo * hitMaterial.emissive) * rayColor;

        duplicateRay.origin = hitpoint + (hitnormal * 0.001);
        vec3 refractDir = duplicateRay.direction;
        float fres = myrefract(refractDir,hitnormal,1.333);
        float choice = RandomFloat01(rngState);
        if (choice*hitMaterial.refractive > fres){ //refract
            duplicateRay.direction = mix(refractDir,normalize(hitnormal + RandomUnitVector(rngState)), hitMaterial.roughness);
            duplicateRay.origin = hitpoint + refractDir*0.001;
            rayColor *= hitMaterial.albedo;//mix(hitMaterial.albedo, hitMaterial.specularColor, doSpecular);
            //duplicateRay.direction = reflect(duplicateRay.direction, hitnormal);
        } else { //reflect
            float doSpecular = (RandomFloat01(rngState) < hitMaterial.metallness) ? 1.0 : 0.0;
            vec3 diffuseDir = normalize(hitnormal + RandomUnitVector(rngState));
            vec3 specularDir = reflect(duplicateRay.direction, hitnormal);
            specularDir = normalize(mix(specularDir, diffuseDir, hitMaterial.roughness * hitMaterial.roughness));
            duplicateRay.direction = mix(diffuseDir, specularDir, doSpecular);
            rayColor *= mix(hitMaterial.albedo, hitMaterial.specularColor, doSpecular);
        }

        
        
    }
    return color;
}

vec3 PathTrace(rayStruct ray){
    vec3 color = vec3(0);
    for (int smpl=0; smpl<u_max_samples; smpl++){
        color += rayTraceSample(ray, smpl).rgb;
    }
    return color / u_max_samples;
}


//----------------------------------------------------------------------------------------------------------
// main
//----------------------------------------------------------------------------------------------------------

mat2 rotate(float a){
    float s = sin(a);
    float c = cos(a);
    return mat2(c, -s, s, c);
}

void main()
{   
    vec2 aspect_ratio = u_resolution/u_resolution.y;
    rngState = uint(uint(gl_FragCoord.x) * uint(1973) + uint(gl_FragCoord.y) * uint(9277) + uint(u_frame) * uint(26699)) | uint(1);
    vec2 jitter = (vec2(RandomFloat01(rngState), RandomFloat01(rngState)) - 0.5)/u_resolution;
    vec2 norm_uv = (v_uv.xy+jitter-0.5)*aspect_ratio;
    
    

    struct rayStruct ray;
    ray.origin = u_cameraPos;//vec3(-8,0,0);

    
    ray.direction = normalize( vec3( 0.7,norm_uv.yx ) );
    
    //ray.direction = Rotate(quat, ray.direction);
    ray.direction.xy *= rotate(u_mousePos.y);
    ray.direction.zx *= rotate(u_mousePos.x);
    
    //materialStruct hitMaterial;
    //vec3 hitpoint = vec3(0);
    //vec3 hitnormal = vec3(0);
    //bool raycastResult = raycast( ray.origin, ray.direction, hitMaterial, hitpoint, hitnormal );
    ////bool res = raycast
//
    //vec3 color = vec3(0); ////rayTraceSample(ray);
    //if (raycastResult == true){
    //    color = vec3(length(hitpoint-ray.origin))/20; //DEPTH
    //    //color = hitnormal;
    //}
    vec3 color = PathTrace(ray);
    fragColor = vec4(color,1.0);//texture(u_geometry_texture, vec2(float(0+2.5)/u_geometry_pixel_count,0));//
}