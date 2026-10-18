#include <cassert>
#include <cstring>
#include <new>
struct KeyFrame { double mTimeStamp; };
struct LocalMapping {
    LocalMapping() {} // surrogate for the pinned constructor's omitted fields
    double mFirstTs;
    KeyFrame* mpCurrentKeyFrame;
    double GetCurrKFTime();
};
struct Atlas { bool initialized = false; bool isImuInitialized() { return initialized; } };
struct System {
    LocalMapping* mpLocalMapper;
    Atlas* mpAtlas;
    double GetTimeFromIMUInit();
};
double LocalMapping::GetCurrKFTime()
{

    if (mpCurrentKeyFrame)
    {
        return mpCurrentKeyFrame->mTimeStamp;
    }
    else
        return 0.0;
}
double System::GetTimeFromIMUInit()
{
    double aux = mpLocalMapper->GetCurrKFTime()-mpLocalMapper->mFirstTs;
    if ((aux>0.) && mpAtlas->isImuInitialized())
        return mpLocalMapper->GetCurrKFTime()-mpLocalMapper->mFirstTs;
    else
        return 0.f;
}
int main() {
    alignas(LocalMapping) unsigned char storage[sizeof(LocalMapping)];
    std::memset(storage, 0xa5, sizeof(storage));
    LocalMapping* mapping = new (storage) LocalMapping;
    assert(mapping->mpCurrentKeyFrame == nullptr);
    assert(mapping->mFirstTs == 0.0);
    assert(mapping->GetCurrKFTime() == 0.0);
    Atlas atlas;
    System system{mapping, &atlas};
    assert(system.GetTimeFromIMUInit() == 0.0);
    KeyFrame frame{11.0}; // synthetic seconds in one shared camera/IMU clock
    mapping->mpCurrentKeyFrame = &frame;
    mapping->mFirstTs = 10.0;
    assert(mapping->GetCurrKFTime() == 11.0);
    assert(system.GetTimeFromIMUInit() == 0.0);
    atlas.initialized = true;
    assert(system.GetTimeFromIMUInit() == 1.0);
    frame.mTimeStamp = 10.0;
    assert(system.GetTimeFromIMUInit() == 0.0);
    mapping->~LocalMapping();
}
