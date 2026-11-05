/* Same ITK classes, 255-bin profile and entropy reductions as ImageMutualInformation1.
 * Image I/O is replaced by in-memory pixel buffers; computation stays in ITK. */
#include "itkImage.h"
#include "itkJoinImageFilter.h"
#include "itkImageToHistogramFilter.h"
#include <algorithm>
#include <cmath>
extern "C" int lassi_mutual_information(int width,int height,const unsigned char *a,const unsigned char *b,double *joint,double *stats) {
  using Image=itk::Image<unsigned char,2>;
  using Join=itk::JoinImageFilter<Image,Image>;
  using Filter=itk::Statistics::ImageToHistogramFilter<Join::OutputImageType>;
  try {
    Image::SizeType size={{static_cast<unsigned long>(width),static_cast<unsigned long>(height)}};
    Image::RegionType region(size);
    auto first=Image::New(),second=Image::New();
    first->SetRegions(region);second->SetRegions(region);first->Allocate();second->Allocate();
    std::copy(a,a+(size_t)width*height,first->GetBufferPointer());
    std::copy(b,b+(size_t)width*height,second->GetBufferPointer());
    auto join=Join::New();join->SetInput1(first);join->SetInput2(second);join->Update();
    auto filter=Filter::New();filter->SetInput(join->GetOutput());filter->SetMarginalScale(10.0);
    filter->SetNumberOfWorkUnits(1);filter->SetAutoMinimumMaximum(false);
    Filter::HistogramMeasurementVectorType low(2),high(2);low.Fill(-0.5);high.Fill(255.5);
    filter->SetHistogramBinMinimum(low);filter->SetHistogramBinMaximum(high);
    for(int pass=0;pass<3;++pass) {
      Filter::HistogramSizeType bins(2);bins[0]=pass==2?1:255;bins[1]=pass==1?1:255;
      filter->SetHistogramSize(bins);filter->Update();
      const auto *hist=filter->GetOutput();double entropy=0,total=hist->GetTotalFrequency();
      for(auto i=hist->Begin();i!=hist->End();++i) {
        const double count=i.GetFrequency();
        if(pass==0) joint[i.GetInstanceIdentifier()]=count;
        if(count>0) {double probability=count/total;entropy-=probability*std::log(probability)/std::log(2.0);}
      }
      stats[pass+1]=entropy;
    }
    stats[0]=stats[2]+stats[3]-stats[1];return 0;
  } catch(const itk::ExceptionObject &e) {std::cerr<<e<<std::endl;return 1;}
}
