#ifndef ELEGANT_NPY_TYPEHELPERS_H
#define ELEGANT_NPY_TYPEHELPERS_H

#include "typehelper.h"
#include "reader.h"
#include "writer.h"
#include "common.h"

#include <assert.h>
#include <armadillo>

namespace elegant {
namespace npy {

template<typename eT> struct TypeHelper<std::vector<eT>, bool> : public BaseTypeHelper<std::vector<eT>, bool> {};
template<typename eT, typename npyT>
struct TypeHelper<std::vector<eT>, npyT> : public BaseTypeHelper<std::vector<eT>, npyT>
{
    using ObjectType = std::vector<eT>;
    using ElementType = eT;
    ObjectType fromFile(const std::vector<size_t> &shape, Reader &reader) {
        if(std::is_same<eT, npyT>::value) {
            ObjectType object(elementCount(shape));
            reader.read(reinterpret_cast<char*>(&object[0]), elementCount(shape) * sizeof(eT));
            return object;
        } else {
            std::vector<npyT> sourceObject = TypeHelper<std::vector<npyT>, npyT>().fromFile(shape, reader);
            ObjectType targetObject(elementCount(shape));
            copy(sourceObject.begin(), sourceObject.end(), targetObject.begin());
            return targetObject;
        }
    }
    bool isSame() {
        return std::is_same<eT, npyT>::value;
    }
    bool isLossyConvertible() {
        return std::is_convertible<eT, npyT>::value;
    }
};

template<typename eT> struct TypeHelper<arma::Mat<eT>, bool> : public BaseTypeHelper<arma::Mat<eT>, bool> {};
template<typename eT> struct TypeHelper<arma::Mat<eT>, int8_t> : public BaseTypeHelper<arma::Mat<eT>, int8_t> {};

template<typename eT, typename npyT>
struct TypeHelper<arma::Mat<eT>, npyT> : public BaseTypeHelper<arma::Mat<eT>, npyT>
{
    using ObjectType = arma::Mat<eT>;
    using ElementType = eT;
    ObjectType fromFile(const std::vector<size_t> &sourceShape, Reader &reader) {
        auto shape = std::vector<size_t>({1, 1, 1});
        if(sourceShape.size() > 2) {
            std::stringstream error;
            error << "Cannot convert object with " << sourceShape.size() << " dimensions to arma::Mat.";
            throw std::runtime_error(error.str());
        } else if(sourceShape.size() == 1) {
            // TODO verify that this is correct and should not be {N, 1}
            shape = {1, sourceShape[0]};
        } else {
            shape = sourceShape;
        }
        if(std::is_same<eT, npyT>::value) {
            int rowCount = shape[0];
            int columnCount = shape[1];
            if(!reader.isFortranOrder()) {
                // swap row and column count because we need to transpose after reading
                rowCount = shape[1];
                columnCount = shape[0];
            }
            ObjectType object(rowCount, columnCount);
            reader.read(reinterpret_cast<char*>(&object[0]), sizeof(eT) * elementCount(shape));
            if(!reader.isFortranOrder()) {
                object = object.t();
            }
            return object;
        } else {
            return arma::conv_to<arma::Mat<eT>>::from(TypeHelper<arma::Mat<npyT>, npyT>().fromFile(shape, reader));
        }
    }
    void toFile(const ObjectType& object, Writer &writer) {
        writer.setFortranOrder(true);
        writer.write(reinterpret_cast<const char*>(&object[0]), {object.n_rows, object.n_cols});
    }
    bool isSame() {
        return std::is_same<eT, npyT>::value;
    }
    bool isLossyConvertible() {
        return std::is_convertible<eT, npyT>::value;
    }
};

template<typename eT> struct TypeHelper<arma::Cube<eT>, bool> : public BaseTypeHelper<arma::Cube<eT>, bool> {};
template<typename eT> struct TypeHelper<arma::Cube<eT>, int8_t> : public BaseTypeHelper<arma::Cube<eT>, int8_t> {};

template<typename eT, typename npyT>
struct TypeHelper<arma::Cube<eT>, npyT> : public BaseTypeHelper<arma::Cube<eT>, npyT>
{
    using ObjectType = arma::Cube<eT>;
    using ElementType = eT;
    ObjectType fromFile(const std::vector<size_t> &sourceShape, Reader &reader) {
        auto shape = std::vector<size_t>({1, 1, 1});
        if(sourceShape.size() > 3) {
            std::stringstream error;
            error << "Cannot convert object with " << sourceShape.size() << " dimensions to arma::Cube.";
            throw std::runtime_error(error.str());
        } else if(sourceShape.size() == 2) {
            shape = {1, sourceShape[0], sourceShape[1]};
        } else if(sourceShape.size() == 1) {
            shape = {1, 1, sourceShape[0]};
        } else {
            shape = sourceShape;
        }
        if(std::is_same<eT, npyT>::value) {
            ObjectType rotated(shape[2], shape[1], shape[0]);
            reader.read(reinterpret_cast<char*>(&rotated[0]), sizeof(eT) * elementCount(shape));
            ObjectType object = arma::Cube<eT>(rotated.n_cols, rotated.n_rows, rotated.n_slices); // swap n_rows and n_cols (col-major to row-major)
            for(int i = 0; i < int(object.n_slices); i++) {
                object.slice(i) = rotated.slice(i).t();
            }
            return object;
        } else {
            return arma::conv_to<arma::Cube<eT>>::from(TypeHelper<arma::Cube<npyT>, npyT>().fromFile(shape, reader));
        }
    }
    void toFile(const ObjectType& object, Writer &writer) {
        ObjectType rotated(object.n_cols, object.n_rows, object.n_slices); // swap n_rows and n_cols (col-major to row-major)
        for(int i = 0; i < int(object.n_slices); i++) {
            rotated.slice(i) = object.slice(i).t();
        }
        writer.setFortranOrder(false);
        writer.write(reinterpret_cast<const char*>(&rotated[0]), {object.n_slices, object.n_rows, object.n_cols});
    }
    bool isSame() {
        return std::is_same<eT, npyT>::value;
    }
    bool isLossyConvertible() {
        return std::is_convertible<eT, npyT>::value;
    }
};

}
}

#endif // ELEGANT_NPY_TYPEHELPERS_H

