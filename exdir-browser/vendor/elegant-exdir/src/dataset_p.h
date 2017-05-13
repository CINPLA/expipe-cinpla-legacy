#ifndef DATASET_P_H
#define DATASET_P_H

#include "io/reader.h"
#include "io/writer.h"

namespace elegant {
namespace exdir {

class Dataset;

class DatasetWriter : public Writer
{
public:
    DatasetWriter(Dataset* dataset);
    virtual void write(const void *buffer) override;
private:
    Dataset* m_dataset = nullptr;
};

class DatasetReader : public Reader
{
public:
    DatasetReader();
    virtual void read(void *buffer) override;
private:
};

}
}

#endif // DATASET_P_H
