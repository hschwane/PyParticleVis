#version 450
//#extension GL_ARB_conservative_depth : require
//layout (depth_greater) out float gl_FragDepth; // enable early depth test
#define PI 3.14159265359f
#define TWOPI 6.28318530718f

struct Material
{
    vec3 ambient;
    vec3 diffuse;
    vec3 specular;
    float shininess;
    float alpha;
};

struct Light
{
    vec3 position;
    vec3 diffuse;
    vec3 specular;
};

in vec2 texcoord;
in vec3 color;
in float radius;
in vec4 viewSphereCenter;
in vec4 viewPosOnPlane;

out vec4 fragment_color;

uniform vec3 lightPosition; // position of the ligth
uniform vec3 lightDiffuse; // diffuse color of the light
uniform vec3 lightSpecular; // specular color of the light

uniform vec3 ambientLight; // ambient light color
uniform bool lightInViewSpace; // is light position in camera / view coordinates? or in wolrd coordinstes?

uniform float materialAlpha; // material alpha value
uniform float materialShininess; // material shininess
// material color is defined in vertex shader

uniform bool renderFlatDisks; // render disks instead of spheres
uniform bool flatFalloff; // apply color falloff from center when using flat shading

uniform bool enableEdgeHighlights; // draw dark rings on the edges

uniform mat4 view; // view matrix
uniform mat4 projection; // projection matrix

uniform bool useTexture; // use a texture together with the color
uniform bool uvUpY; // use z as up for texture coordinates
uniform sampler2D colorTexture; // texture to use

// calculate 3d position on the sphere
// returns false if we are not on the sphere
// see https://github.com/tdd11235813/spheres_shader/tree/master/src/shader
// and: https://paroj.github.io/gltut/Illumination/Tutorial%2013.html
// as well as chapter 14 and 15
// for sphere imposter rendering
bool ImposterSphere(in const vec3 viewPosOnPlane, in const vec3 viewSphereCenter, in const float radius, out vec3 viewNormal, out vec3 viewPosOnSphere)
{
    // do raytracing to check if we see the sphere
    const vec3 rayDirection = normalize(viewPosOnPlane);

    // solution of ray, sphere intersection (quadratic equation)
    const float B = -2.0f * dot(rayDirection, viewSphereCenter);
    const float C = dot(viewSphereCenter, viewSphereCenter) - (radius * radius);

    const float det = (B * B) - (4.0f * C);
    if(det < 0.0)
        return false;

    const float sqrtDet = sqrt(det);
    const float posT = (-B + sqrtDet)/2.0f;
    const float negT = (-B - sqrtDet)/2.0f;

    // two solutions for t choose the closer one
    const float intersectT = min(posT, negT);

    // compute normal and position in view space
    viewPosOnSphere = rayDirection * intersectT;
    viewNormal = normalize(viewPosOnSphere - viewSphereCenter);
    return true;
}

// computes texture coordinates for the sphere
vec2 getUVCoords(in const vec3 viewSphereCenter, in const float radius, in const vec3 viewNormal)
{
    vec3 viewPos= viewSphereCenter + viewNormal*radius;
    mat4 invView = inverse(view);
    vec3 posWorld = vec3(invView * vec4(viewPos,1));
    vec3 centerWorld = vec3(invView * vec4(viewSphereCenter,1));
    vec3 pos = posWorld - centerWorld;
    vec2 uv;

    if(!uvUpY)
        pos.xyz = pos.xzy;

    float phi = acos(pos.z / radius);
    vec2 spherical = vec2(  atan(pos.y,pos.x), phi);
    uv = vec2( (PI+spherical.x) / TWOPI, spherical.y / PI);

    return uv;
}

// computes blinn phong lighting
vec3 BlinnPhong(in const Material mat, in const Light light, in const vec3 viewPosition, in const vec3 viewDir, in const vec3 viewNormal)
{
    // compute light pos in view space
    vec3 viewLightPos;
    if(lightInViewSpace)
        viewLightPos = light.position.xyz;
    else
        viewLightPos = (view * vec4(light.position.xyz,1.0f)).xyz;

    // compute required directions
    const vec3 lightDir = normalize(viewLightPos-viewPosition);

    const vec3 halfAngle = normalize(lightDir + viewDir);
    const vec3 reflectDir = reflect(-lightDir, viewNormal);

    // light multiplier
    const float phi = max( dot(viewNormal, lightDir), 0.0f); // diffuse
    const float psi = pow(max(dot(viewNormal, halfAngle), 0.0f), mat.shininess); // specular

    return phi * mat.diffuse * light.diffuse + psi * mat.specular * light.specular;
}

void main()
{
    // define material
    Material mat = Material(  vec3(color.rgb),
                                    vec3(color.rgb),
                                    vec3(color.rgb),
                                    materialShininess,
                                    materialAlpha);

    // define light
    const Light light = Light(lightPosition,lightDiffuse,lightSpecular);

    if(renderFlatDisks)
    {
        // render as a flat disc
        float distFromCenter = length(texcoord);

        // make it round
        if(distFromCenter > 1.0f)
        {
            discard;
        }

        // set the depth (since quads are rendered in front of actual)
        const vec4 clipPos = projection * viewPosOnPlane;
        gl_FragDepth = ((gl_DepthRange.diff * (clipPos.z / clipPos.w)) + gl_DepthRange.near + gl_DepthRange.far) / 2.0f;

        // set color
        fragment_color = vec4(mat.diffuse,mat.alpha);
        if(flatFalloff)
            fragment_color *= (1-distFromCenter);
    }
    else
    {
        // render as a sphere imposter
        vec3 viewPosOnSphere;
        vec3 viewNormal;
        if( ImposterSphere(viewPosOnPlane.xyz,viewSphereCenter.xyz,radius,viewNormal,viewPosOnSphere)) // we are on the sphere
        {
            // set the depth
            const vec4 clipPos = projection * vec4(viewPosOnSphere, 1.0f);
            gl_FragDepth = ((gl_DepthRange.diff * (clipPos.z / clipPos.w)) + gl_DepthRange.near + gl_DepthRange.far) / 2.0f;

            // texturing
            if(useTexture)
            {
                // calculate uv coordinates on the sphere in latitude logitude space
                vec2 uv = getUVCoords(viewSphereCenter.xyz,radius,viewNormal);
                vec3 texColor = texture(colorTexture, uv).xyz;
                mat.diffuse *= texColor;
                mat.specular *= texColor;
                mat.ambient *= texColor;
            }

            // lighting
            const vec3 viewDir = normalize(-viewPosOnSphere);
            const vec3 color = BlinnPhong(mat, light, viewPosOnSphere, viewDir, viewNormal);
            fragment_color = vec4(mat.ambient * ambientLight + color, mat.alpha);

            if(enableEdgeHighlights && dot(viewNormal,viewDir) < 0.3)
                fragment_color.xyz = vec3(0);

        }
        else // we are not on the sphere
        {
            discard;
        }
    }
}